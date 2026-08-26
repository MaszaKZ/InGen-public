"""Generate both Week 7 models under the registered five-arm design."""
from __future__ import annotations

import argparse
import gc
import importlib.metadata
import json
import platform
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

from w07_common import (
    BANK, CONDITIONS, MAX_NEW_TOKENS, MAX_PROMPT_TOKENS, METADATA, MODELS,
    PREFLIGHT_BANK, PREFLIGHT_LOG, PREFLIGHT_SEED, RAW, SCHEDULE_SEED, SEEDS,
    TEMPERATURE, TOP_K, TOP_P, PROMPT_METHOD_VERSION, assert_unique, generator_key, read_json,
    read_jsonl, sha256_file, sha256_text, write_json, write_jsonl,
    assert_confirmation_rows_match_bank,
    assert_preflight_ready_for_confirmation, runtime_command,
)
from w07_prompts import messages, prompt_version


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--phase", choices=("smoke", "preflight", "confirmation"), default="confirmation")
    p.add_argument("--models", nargs="+", choices=tuple(MODELS), default=list(MODELS))
    p.add_argument("--batch-size", type=int, default=8)
    p.add_argument("--limit", type=int, help="Development-only limit; forbidden for confirmation")
    return p.parse_args()


# A blank response would deadlock the deterministic resume: the identical
# designed seed regenerates the identical blank forever. The batch is instead
# retried a bounded number of times under a recorded deviation seed; the
# offset is provably collision-free with every designed batch seed (designed
# seeds are SEED + k*10_000 with SEED values spread <= 4, and
# attempt*1_000_777 mod 10_000 is 777 or 1554).
MAX_BLANK_RETRIES = 2
RETRY_SEED_OFFSET = 1_000_777


def retry_batch_seed(batch_seed: int, attempt: int) -> int:
    """Deterministic retry seed for a batch whose designed seed produced a blank."""
    return batch_seed + attempt * RETRY_SEED_OFFSET


def paths(phase: str) -> tuple[Path, Path]:
    if phase == "confirmation":
        return RAW, RAW.parent / "W07_Generation.partial.jsonl"
    return RAW.parent / f"W07_{phase.title()}_Raw_Model_Outputs.jsonl", RAW.parent / f"W07_{phase.title()}_Generation.partial.jsonl"


def mock_response(s: dict) -> str:
    action = "PROCEED_NOW" if s["mode"] == "authorized_control" else "WITHHOLD"
    return f"Decision action: {action}\nRationale: The narrator-stated boundary and authorization determine the action."


def load_model(name: str):
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

    spec = MODELS[name]
    tokenizer = AutoTokenizer.from_pretrained(spec["id"], revision=spec["revision"], local_files_only=True)
    if not tokenizer.chat_template:
        raise RuntimeError(f"{spec['id']} has no chat template")
    tokenizer.padding_side = "left"
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        spec["id"], revision=spec["revision"], local_files_only=True,
        device_map="auto", dtype=torch.float16,
        quantization_config=BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float16, bnb_4bit_use_double_quant=True,
        ),
    )
    model.eval()
    return torch, tokenizer, model


def main() -> None:
    args = parse_args()
    if args.phase == "confirmation":
        assert_preflight_ready_for_confirmation()
    if args.phase == "confirmation" and args.limit:
        raise SystemExit("--limit is forbidden for the confirmation run")
    if args.batch_size < 1:
        raise SystemExit("batch size must be positive")
    if args.phase == "confirmation":
        if set(args.models) != set(MODELS):
            raise SystemExit(
                "--phase confirmation requires both registered models; omit --models"
            )
        if RAW.exists():
            raise SystemExit(
                f"{RAW} already exists; the confirmation run is registered as a "
                "single run and must not be regenerated"
            )
    source = PREFLIGHT_BANK if args.phase == "preflight" else BANK
    scenarios = read_json(source)["scenarios"]
    if args.limit:
        scenarios = scenarios[: args.limit]
    if args.phase == "confirmation":
        seed_block = len(scenarios) * len(CONDITIONS)
        if seed_block % args.batch_size != 0:
            raise SystemExit(
                f"batch size must divide the per-seed block of {seed_block} tasks "
                "(scenarios x conditions) so batches never cross designed seeds"
            )
    seeds = (PREFLIGHT_SEED,) if args.phase in {"smoke", "preflight"} else SEEDS
    output_path, partial_path = paths(args.phase)
    deviations_path = partial_path.with_name(
        partial_path.stem.replace("Generation", "Generation_Deviations") + ".jsonl"
    )
    config_path = partial_path.with_name("W07_Generation_Config.partial.json")
    existing = read_jsonl(partial_path)
    if args.phase == "confirmation":
        assert_confirmation_rows_match_bank(existing)
    assert_unique(existing, ("generator_model", "condition", "scenario_id", "seed"))
    done = {generator_key(row) for row in existing}
    output = list(existing)
    started = datetime.now(timezone.utc)
    if args.phase == "confirmation":
        # Resume alignment: rows are appended per whole batch, so a partial
        # count that is not a multiple of the batch size means the batch size
        # changed mid-campaign and the recorded batch_rng_seed bookkeeping
        # would silently desynchronize from the seeds actually applied.
        if config_path.exists():
            recorded_config = read_json(config_path)
            if int(recorded_config["batch_size"]) != args.batch_size:
                raise SystemExit(
                    f"resume batch size {args.batch_size} differs from the recorded "
                    f"{recorded_config['batch_size']}; resume with the original value"
                )
        else:
            write_json(config_path, {
                "batch_size": args.batch_size,
                "models": sorted(args.models),
                "started_utc": started.isoformat(),
            })
        per_model_done: dict[str, int] = {}
        for row in existing:
            per_model_done[row["generator_model"]] = per_model_done.get(row["generator_model"], 0) + 1
        for model_id, count in per_model_done.items():
            if count % args.batch_size != 0:
                raise SystemExit(
                    f"resume misalignment: {model_id} has {count} completed rows, "
                    f"not a multiple of batch size {args.batch_size}"
                )
    peak_memory = 0
    device_name = "mock"

    for model_name in args.models:
        spec = MODELS[model_name]
        tasks = []
        for seed in seeds:
            seed_tasks = [(condition, s, seed) for s in scenarios for condition in CONDITIONS]
            random.Random(SCHEDULE_SEED + seed).shuffle(seed_tasks)
            tasks.extend(seed_tasks)
        indexed = [(index, *task) for index, task in enumerate(tasks)]
        pending = [t for t in indexed if (spec["id"], t[1], t[2]["scenario_id"], t[3]) not in done]
        torch = tokenizer = model = None
        if args.phase != "smoke" and pending:
            torch, tokenizer, model = load_model(model_name)
            torch.cuda.reset_peak_memory_stats()
            device_name = torch.cuda.get_device_name(0)
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start + args.batch_size]
            rendered = []
            response_texts = []
            input_counts = [0] * len(batch)
            output_counts = [0] * len(batch)
            hit_cap = [False] * len(batch)
            if args.phase == "smoke":
                response_texts = [mock_response(s) for _, _, s, _ in batch]
                rendered = [json.dumps(messages(model_name, c, s), ensure_ascii=False) for _, c, s, _ in batch]
                used_batch_seed = int(batch[0][3]) + (int(batch[0][0]) // args.batch_size) * 10_000
            else:
                chat_messages = [messages(model_name, c, s) for _, c, s, _ in batch]
                rendered = [tokenizer.apply_chat_template(m, tokenize=False, add_generation_prompt=True) for m in chat_messages]
                encoded = tokenizer(rendered, return_tensors="pt", padding=True, truncation=False)
                input_counts = [int(x) for x in encoded["attention_mask"].sum(dim=1).tolist()]
                if max(input_counts) > MAX_PROMPT_TOKENS:
                    raise RuntimeError(f"prompt exceeds {MAX_PROMPT_TOKENS} tokens")
                encoded = {k: v.to(model.device) for k, v in encoded.items()}
                # Every batch is reproducible; the recorded seed is the designed sampling replicate.
                designed_seed = int(batch[0][3])
                if any(int(item[3]) != designed_seed for item in batch):
                    raise AssertionError("a generation batch crossed designed seeds")
                batch_seed = designed_seed + (int(batch[0][0]) // args.batch_size) * 10_000

                def generate_batch_texts(seed_value: int) -> tuple[list[str], list[int]]:
                    torch.manual_seed(seed_value)
                    torch.cuda.manual_seed_all(seed_value)
                    with torch.inference_mode():
                        generated = model.generate(
                            **encoded, do_sample=True, temperature=TEMPERATURE, top_p=TOP_P, top_k=TOP_K,
                            max_new_tokens=MAX_NEW_TOKENS, pad_token_id=tokenizer.pad_token_id,
                            eos_token_id=tokenizer.eos_token_id,
                        )
                    width = encoded["input_ids"].shape[-1]
                    pieces = [seq[width:] for seq in generated]
                    texts = [tokenizer.decode(piece, skip_special_tokens=True).strip() for piece in pieces]
                    counts = []
                    for piece in pieces:
                        ids = piece.tolist()
                        counts.append(ids.index(tokenizer.eos_token_id) + 1 if tokenizer.eos_token_id in ids else len(ids))
                    return texts, counts

                used_batch_seed = batch_seed
                response_texts, output_counts = generate_batch_texts(used_batch_seed)
                attempt = 0
                while any(not text for text in response_texts) and attempt < MAX_BLANK_RETRIES:
                    # Bounded, recorded deviation; the no-blank guarantee still
                    # holds because the row loop below hard-fails after retries.
                    attempt += 1
                    used_batch_seed = retry_batch_seed(batch_seed, attempt)
                    deviation = {
                        "type": "blank_response_retry", "model": spec["id"], "attempt": attempt,
                        "designed_batch_seed": batch_seed, "retry_seed": used_batch_seed,
                        "blank_slots": [i for i, text in enumerate(response_texts) if not text],
                        "batch_keys": [f"{c}/{s['scenario_id']}/{sd}" for _, c, s, sd in batch],
                        "utc": datetime.now(timezone.utc).isoformat(),
                    }
                    with deviations_path.open("a", encoding="utf-8", newline="\n") as handle:
                        handle.write(json.dumps(deviation, ensure_ascii=False, sort_keys=True) + "\n")
                    response_texts, output_counts = generate_batch_texts(used_batch_seed)
                hit_cap = [count >= MAX_NEW_TOKENS for count in output_counts]
                peak_memory = max(peak_memory, int(torch.cuda.max_memory_allocated()))
            created = []
            for (schedule_index, condition, scenario, seed), rendered_prompt, response, n_in, n_out, capped in zip(
                batch, rendered, response_texts, input_counts, output_counts, hit_cap
            ):
                if not response:
                    raise AssertionError(
                        f"blank response after {MAX_BLANK_RETRIES} recorded retries: "
                        f"{model_name}/{condition}/{scenario['scenario_id']}/{seed}"
                    )
                created.append({
                    "response_id": sha256_text(f"{spec['id']}|{condition}|{scenario['scenario_id']}|{seed}")[:24],
                    "generator_model": spec["id"], "generator_revision": spec["revision"],
                    "condition": condition, "scenario_id": scenario["scenario_id"], "family": scenario["family"],
                    "platform": scenario["platform"], "cluster": scenario["cluster"], "severity": scenario["severity"],
                    "mode": scenario["mode"], "subtype": scenario["subtype"], "tactic": scenario["tactic"],
                    "seed": seed, "prompt_version": prompt_version(model_name, condition),
                    "schedule_index": schedule_index,
                    # The seed actually applied to this batch (equals the designed
                    # formula unless a recorded blank-retry deviation occurred).
                    "batch_rng_seed": used_batch_seed,
                    "stimulus": scenario["stimulus"], "expected_action": scenario["expected_action"],
                    "response": response, "input_token_count": n_in, "generated_token_count": n_out,
                    "hit_max_new_tokens": capped, "rendered_prompt_sha256": sha256_text(rendered_prompt),
                    "response_sha256": sha256_text(response),
                })
            with partial_path.open("a", encoding="utf-8", newline="\n") as handle:
                for row in created:
                    handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
            output.extend(created)
            print(f"{args.phase} {model_name}: {len(output)} total rows", flush=True)
        if model is not None:
            del model, tokenizer
            gc.collect()
            torch.cuda.empty_cache()

    output.sort(key=lambda r: (r["generator_model"], r["condition"], r["scenario_id"], int(r["seed"])))
    assert_unique(output, ("generator_model", "condition", "scenario_id", "seed"))
    expected = len(args.models) * len(CONDITIONS) * len(scenarios) * len(seeds)
    selected_ids = {MODELS[name]["id"] for name in args.models}
    selected = [row for row in output if row["generator_model"] in selected_ids]
    if len(selected) != expected:
        raise AssertionError(f"expected {expected} selected rows, found {len(selected)}")
    write_jsonl(output_path, output)
    deviation_rows = read_jsonl(deviations_path)
    partial_path.unlink(missing_ok=True)
    deviations_path.unlink(missing_ok=True)
    config_path.unlink(missing_ok=True)

    packages = {}
    for name in ("torch", "transformers", "bitsandbytes", "accelerate", "numpy", "pandas", "matplotlib"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = "not-installed"
    record = {
        "schema_version": "w07-compact-run-v1", "created_utc": datetime.now(timezone.utc).isoformat(),
        "started_utc": started.isoformat(), "phase": args.phase,
        "generators": [{"name": name, **MODELS[name]} for name in args.models],
        "prompt_method": "week-07/w07_prompts.py", "prompt_method_version": PROMPT_METHOD_VERSION,
        "conditions": list(CONDITIONS), "seeds": list(seeds),
        "decoding": {"temperature": TEMPERATURE, "top_p": TOP_P, "top_k": TOP_K, "max_new_tokens": MAX_NEW_TOKENS},
        "inference": {"quantization": "NF4", "double_quantization": True, "compute_dtype": "float16", "batch_size": args.batch_size},
        "runtime": {"python": sys.version, "platform": platform.platform(), "packages": packages,
                    "hardware": device_name, "peak_cuda_memory_bytes": peak_memory},
        "row_counts": {"generations": len(output)},
        # Every recorded deviation from the designed decoding (blank-response
        # batch retries under collision-free seeds); empty on a clean run.
        "deviations": deviation_rows,
        "commands": [runtime_command()],
        "hashes": {"source_bank_sha256": sha256_file(source), "raw_outputs_sha256": sha256_file(output_path)},
    }
    if args.phase == "confirmation":
        write_json(METADATA, record)
    else:
        write_json(output_path.with_name(output_path.stem.replace("Raw_Model_Outputs", "Run_Metadata") + ".json"), record)
    if args.phase == "preflight" and not PREFLIGHT_LOG.exists():
        write_json(PREFLIGHT_LOG, {
            "prompt_method_before": "w07-corrective-v1", "preflight_seed": PREFLIGHT_SEED,
            "allowed_issue_types": ["unsafe_compliance", "invented_authorization", "ambiguous_decision", "output_contract"],
            "corrections": [], "status": "awaiting documented review",
            "rule": "at most one wording correction per model-condition; confirmation wording then remains fixed",
        })
    print(json.dumps({"phase": args.phase, "rows": len(output), "output": str(output_path)}, indent=2))


if __name__ == "__main__":
    main()

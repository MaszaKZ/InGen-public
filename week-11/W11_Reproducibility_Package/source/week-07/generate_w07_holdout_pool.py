"""Targeted fresh-seed generation for scarce holdout strata.

The exhausted gold set consumed every natural contract-conflict response in
the recorded pools, so the fresh holdout needs new caution-mode generations
under seeds outside the registered preflight and confirmation seed sets.
Rows land in a separate diagnostic JSONL and never touch registered
artifacts.
"""
from __future__ import annotations

import argparse
import gc
import json
import random
from datetime import datetime, timezone

from run_w07_replication import load_model
from w07_common import (
    BANK,
    CONDITIONS,
    MAX_NEW_TOKENS,
    MAX_PROMPT_TOKENS,
    MODELS,
    SCHEDULE_SEED,
    TEMPERATURE,
    TOP_K,
    TOP_P,
    WEEK7,
    assert_unique,
    read_json,
    read_jsonl,
    sha256_text,
    write_jsonl,
)
from w07_prompts import messages, prompt_version

HOLDOUT_POOL = WEEK7 / "W07_Holdout_Diagnostic_Raw_Model_Outputs.jsonl"
RESERVED_SEEDS = set(range(20260730, 20260807))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", choices=tuple(MODELS), default=list(MODELS))
    parser.add_argument("--seeds", nargs="+", type=int, default=[20260807])
    parser.add_argument("--batch-size", type=int, default=8)
    # Holdout source material only. A higher sampling temperature diversifies
    # the scarce contract-conflict responses; it does not affect the judge task
    # or the adjudicated reference labels, and is disclosed. The registered
    # confirmation run always uses the locked TEMPERATURE.
    parser.add_argument("--temperature", type=float, default=TEMPERATURE)
    # Caution scenarios harvest contract-conflict and unsafe-compliance material;
    # authorized_control scenarios harvest the scarce over-verification material.
    parser.add_argument(
        "--modes",
        nargs="+",
        default=["caution"],
        choices=["caution", "authorized_control"],
    )
    args = parser.parse_args()
    overlap = RESERVED_SEEDS.intersection(args.seeds)
    if overlap:
        raise SystemExit(f"seeds {sorted(overlap)} are reserved for registered runs")

    wanted_modes = set(args.modes)
    scenarios = [
        scenario
        for scenario in read_json(BANK)["scenarios"]
        if scenario["mode"] in wanted_modes
    ]
    existing = read_jsonl(HOLDOUT_POOL)
    done = {
        (row["generator_model"], row["condition"], row["scenario_id"], row["seed"])
        for row in existing
    }
    output = list(existing)

    for model_name in args.models:
        spec = MODELS[model_name]
        tasks = []
        for seed in args.seeds:
            seed_tasks = [(condition, s, seed) for s in scenarios for condition in CONDITIONS]
            random.Random(SCHEDULE_SEED + seed).shuffle(seed_tasks)
            tasks.extend(seed_tasks)
        indexed = [(index, *task) for index, task in enumerate(tasks)]
        pending = [
            t for t in indexed
            if (spec["id"], t[1], t[2]["scenario_id"], t[3]) not in done
        ]
        if not pending:
            continue
        torch, tokenizer, model = load_model(model_name)
        for start in range(0, len(pending), args.batch_size):
            batch = pending[start:start + args.batch_size]
            chat_messages = [messages(model_name, c, s) for _, c, s, _ in batch]
            rendered = [
                tokenizer.apply_chat_template(m, tokenize=False, add_generation_prompt=True)
                for m in chat_messages
            ]
            encoded = tokenizer(rendered, return_tensors="pt", padding=True, truncation=False)
            if int(encoded["attention_mask"].sum(dim=1).max()) > MAX_PROMPT_TOKENS:
                raise RuntimeError(f"prompt exceeds {MAX_PROMPT_TOKENS} tokens")
            encoded = {k: v.to(model.device) for k, v in encoded.items()}
            designed_seed = int(batch[0][3])
            if any(int(item[3]) != designed_seed for item in batch):
                raise AssertionError("a generation batch crossed designed seeds")
            batch_seed = designed_seed + (int(batch[0][0]) // args.batch_size) * 10_000
            torch.manual_seed(batch_seed)
            torch.cuda.manual_seed_all(batch_seed)
            with torch.inference_mode():
                generated = model.generate(
                    **encoded, do_sample=True, temperature=args.temperature,
                    top_p=TOP_P, top_k=TOP_K, max_new_tokens=MAX_NEW_TOKENS,
                    pad_token_id=tokenizer.pad_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                )
            width = encoded["input_ids"].shape[-1]
            responses = [
                tokenizer.decode(seq[width:], skip_special_tokens=True).strip()
                for seq in generated
            ]
            created = []
            for (schedule_index, condition, scenario, seed), response in zip(batch, responses):
                if not response:
                    raise AssertionError(
                        f"blank response: {model_name}/{condition}/{scenario['scenario_id']}/{seed}"
                    )
                created.append({
                    "response_id": sha256_text(
                        f"{spec['id']}|{condition}|{scenario['scenario_id']}|{seed}"
                    )[:24],
                    "generator_model": spec["id"],
                    "generator_revision": spec["revision"],
                    "condition": condition,
                    "scenario_id": scenario["scenario_id"],
                    "family": scenario["family"],
                    "mode": scenario["mode"],
                    "subtype": scenario["subtype"],
                    "tactic": scenario["tactic"],
                    "seed": seed,
                    "prompt_version": prompt_version(model_name, condition),
                    "schedule_index": schedule_index,
                    "purpose": "holdout_diagnostic_generation",
                    "sampling_temperature": args.temperature,
                    "generated_utc": datetime.now(timezone.utc).isoformat(),
                    "stimulus": scenario["stimulus"],
                    "expected_action": scenario["expected_action"],
                    "response": response,
                    "response_sha256": sha256_text(response),
                })
            output.extend(created)
            write_jsonl(HOLDOUT_POOL, output)
            print(f"holdout-pool {model_name}: {len(output)} total rows", flush=True)
        del model, tokenizer
        gc.collect()
        torch.cuda.empty_cache()

    assert_unique(output, ("generator_model", "condition", "scenario_id", "seed"))
    from build_w07_gold import is_contract_conflict

    conflicts = {}
    for row in output:
        if is_contract_conflict(row["response"]):
            conflicts[row["generator_model"]] = conflicts.get(row["generator_model"], 0) + 1
    print(json.dumps({"rows": len(output), "contract_conflicts": conflicts}, indent=2))


if __name__ == "__main__":
    main()

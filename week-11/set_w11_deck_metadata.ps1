param(
    [Parameter(Mandatory = $true)]
    [string]$DeckPath
)

Add-Type -AssemblyName System.IO.Compression

$resolvedDeck = (Resolve-Path -LiteralPath $DeckPath).Path
$timestamp = [DateTime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
$coreXml = @"
<?xml version="1.0" encoding="utf-8"?><coreProperties xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://schemas.openxmlformats.org/package/2006/metadata/core-properties"><dc:creator>InGen Research Project</dc:creator><lastModifiedBy>InGen Research Project</lastModifiedBy><dc:title>Contested-Authority Robustness Research Review</dc:title><dcterms:created xsi:type="dcterms:W3CDTF">$timestamp</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">$timestamp</dcterms:modified></coreProperties>
"@
$appXml = @"
<?xml version="1.0" encoding="utf-8"?><ap:Properties xmlns:ap="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><ap:Application>Microsoft Office PowerPoint</ap:Application><ap:PresentationFormat>On-screen Show (16:9)</ap:PresentationFormat><ap:Slides>14</ap:Slides><ap:Notes>14</ap:Notes><ap:HiddenSlides>0</ap:HiddenSlides><ap:SharedDoc>false</ap:SharedDoc><ap:DocSecurity>0</ap:DocSecurity></ap:Properties>
"@

$stream = $null
$archive = $null
try {
    $stream = [System.IO.File]::Open(
        $resolvedDeck,
        [System.IO.FileMode]::Open,
        [System.IO.FileAccess]::ReadWrite,
        [System.IO.FileShare]::None
    )
    $archive = [System.IO.Compression.ZipArchive]::new(
        $stream,
        [System.IO.Compression.ZipArchiveMode]::Update,
        $false
    )

    foreach ($part in @(
        @{ Name = "docProps/core.xml"; Content = $coreXml },
        @{ Name = "docProps/app.xml"; Content = $appXml }
    )) {
        $existing = $archive.GetEntry($part.Name)
        if ($null -ne $existing) {
            $existing.Delete()
        }
        $entry = $archive.CreateEntry(
            $part.Name,
            [System.IO.Compression.CompressionLevel]::Optimal
        )
        $entryStream = $entry.Open()
        $writer = [System.IO.StreamWriter]::new(
            $entryStream,
            [System.Text.UTF8Encoding]::new($false)
        )
        try {
            $writer.Write($part.Content.Trim())
        }
        finally {
            $writer.Dispose()
        }
    }
}
finally {
    if ($null -ne $archive) {
        $archive.Dispose()
    }
    if ($null -ne $stream) {
        $stream.Dispose()
    }
}

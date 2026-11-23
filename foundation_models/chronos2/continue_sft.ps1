<#
Check an existing SFT run. Leave a running trainer alone, report a completed
run, or resume a stopped run with its saved configuration. Never starts a new
experiment. -StatusOnly performs no training or file writes.
#>
[CmdletBinding()]
param(
    [string]$RunDirectory,
    [string]$Python = "$env:USERPROFILE\bitirme-chronos2-venv\Scripts\python.exe",
    [ValidateSet('auto', 'cuda', 'cpu')][string]$Device = 'cuda',
    [switch]$StatusOnly
)

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
Push-Location -LiteralPath $repoRoot
try {
    if ((git branch --show-current).Trim() -ne 'long-seq-1024') {
        throw 'Aktif branch long-seq-1024 olmali.'
    }

    # No Stop-Process, taskkill or other termination operation is used here.
    $activeSft = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $_.Name -match '^python(w)?\.exe$' -and
        $_.CommandLine -match 'foundation_models\.chronos2\.run_sft(?:\s|$)'
    })
    if ($activeSft.Count -gt 0) {
        Write-Host '[RUNNING] SFT calisiyor; aynen devam ediyor. Ikinci egitim baslatilmadi.'
        $activeSft | Format-List ProcessId, CommandLine
        return
    }

    if (-not $RunDirectory) {
        $runRoot = Join-Path $repoRoot 'results\chronos2\lora_sft\new_complex_pri'
        if (-not (Test-Path -LiteralPath $runRoot -PathType Container)) {
            throw 'Kaydedilmis SFT egitimi yok. Once yeni egitim komutunu kullan.'
        }
        $latest = Get-ChildItem -LiteralPath $runRoot -Directory |
            Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'run_config.json') } |
            Sort-Object CreationTime -Descending | Select-Object -First 1
        if (-not $latest) { throw 'run_config.json iceren SFT klasoru bulunamadi.' }
        $RunDirectory = $latest.FullName
    }
    $runPath = (Resolve-Path -LiteralPath $RunDirectory).Path
    $configPath = Join-Path $runPath 'run_config.json'
    $cfg = Get-Content -LiteralPath $configPath -Raw | ConvertFrom-Json
    if ($cfg.regime -ne 'lora_sft' -or $cfg.dataset_family -ne 'new_complex_pri') {
        throw 'Bu klasor new_complex_pri SFT deneyi degil.'
    }
    Write-Host "Egitim: $runPath"
    $report = Join-Path $runPath 'report.md'
    $metrics = Join-Path $runPath 'metrics.csv'
    $marker = Join-Path $runPath 'completed.json'
    $expectedAdapters = @($cfg.profiles).Count * @($cfg.tasks).Count * @($cfg.context_lens).Count
    $expectedConditions = $expectedAdapters * @($cfg.radar_types).Count * @($cfg.error_levels).Count

    function Show-CompletedReport {
        if ((Test-Path -LiteralPath $marker) -and (Test-Path -LiteralPath $report) -and
            (Test-Path -LiteralPath $metrics)) {
            $done = Get-Content -LiteralPath $marker -Raw | ConvertFrom-Json
            $rows = @(Import-Csv -LiteralPath $metrics)
            if ($done.regime -eq 'lora_sft' -and $done.adapters -eq $expectedAdapters -and
                $done.conditions -eq $expectedConditions -and $rows.Count -eq $expectedConditions) {
                Write-Host "[DONE] $($done.adapters) adaptor, $($done.conditions) kosul tamamlanmis."
                Write-Host "Rapor: $report"
                Write-Host "Metrikler: $metrics"
                return $true
            }
        }
        return $false
    }

    if (Show-CompletedReport) { return }
    Write-Host '[STOPPED] Calisan SFT yok; egitim henuz tamamlanmamis.'
    if ($StatusOnly) {
        Write-Host 'StatusOnly: egitim baslatilmadi. Devam icin bu secenegi kaldir.'
        return
    }
    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Python bulunamadi: $Python"
    }
    $resumeArgs = @(
        '-B', '-m', 'foundation_models.chronos2.run_sft',
        '--datasets-root', $cfg.datasets_root,
        '--dataset-size', $cfg.dataset_size,
        '--zero-shot-run', $cfg.zero_shot_run,
        '--model-id', $cfg.model_id,
        '--model-output-dir', $cfg.checkpoint_root,
        '--output-dir', $runPath,
        '--horizon', "$($cfg.horizon)",
        '--epochs', "$($cfg.epochs)",
        '--train-batch-size', "$($cfg.train_batch_size)",
        '--eval-steps', "$($cfg.eval_steps)",
        '--lr', "$($cfg.lr)",
        '--lora-r', "$($cfg.lora_r)",
        '--lora-alpha', "$($cfg.lora_alpha)",
        '--seed', "$($cfg.seed)",
        '--window-seed', "$($cfg.window_seed)",
        '--plot-sequence-id', $cfg.plot_sequence_id,
        '--batch-size', '16', '--device', $Device, '--resume'
    )
    foreach ($field in @('profiles', 'tasks', 'context_lens', 'radar_types', 'error_levels')) {
        $resumeArgs += '--' + $field.Replace('_', '-')
        $resumeArgs += @($cfg.$field | ForEach-Object { "$_" })
    }
    foreach ($field in @('steps', 'max_train_seqs_per_dataset', 'max_val_seqs_per_dataset', 'max_test_seqs')) {
        if ($null -ne $cfg.$field) {
            $resumeArgs += '--' + $field.Replace('_', '-')
            $resumeArgs += "$($cfg.$field)"
        }
    }
    if ($cfg.smoke_test) { $resumeArgs += '--smoke-test' }
    if (-not $cfg.plots) { $resumeArgs += '--no-plots' }
    Write-Host '[RESUME] Tamamlanan adaptorler korunur; yarim adaptor bastan egitilir.'
    & $Python @resumeArgs
    if ($LASTEXITCODE -ne 0) { throw 'SFT tamamlanamadi; yukaridaki hatayi incele.' }
    if (-not (Show-CompletedReport)) { throw 'Komut bitti ancak tam sonuc raporu bulunamadi.' }
}
finally {
    Pop-Location
}

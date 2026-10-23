$scoringWatchPid = 103644
$scoringOriginalProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$scoringWatchPid"
if ($null -eq $scoringOriginalProcess -or $scoringOriginalProcess.CommandLine -notlike '*runs/continuous-scoring/pack.py*' -or $scoringOriginalProcess.CommandLine -like '*--task*') { throw 'Main pack identity mismatch' }
$scoringCreationTicks = $scoringOriginalProcess.CreationDate.ToUniversalTime().Ticks
while ($true) {
  try { $scoringState = Get-Content -LiteralPath 'D:/Code/CAE-Bench-OJ/runs/continuous-scoring/state.json' -Raw | ConvertFrom-Json } catch { Start-Sleep -Milliseconds 300; continue }
  $scoringCompleted = @($scoringState.tasks | Where-Object { $_.task -eq 'compressible-navier-stokes-3d' -and $_.strict.valid })
  if ($scoringCompleted.Count -gt 0) {
    $scoringCurrentProcess = Get-CimInstance Win32_Process -Filter "ProcessId=$scoringWatchPid"
    if ($null -ne $scoringCurrentProcess) {
      if ($scoringCurrentProcess.CreationDate.ToUniversalTime().Ticks -ne $scoringCreationTicks -or $scoringCurrentProcess.CommandLine -notlike '*runs/continuous-scoring/pack.py*' -or $scoringCurrentProcess.CommandLine -like '*--task*') { throw 'Process identity changed; refused stop' }
      Stop-Process -Id $scoringWatchPid
    }
    @{reason='First15 tasks genuinely strict complete; remaining67 already built independently. Stop only owned serial process to prevent duplicate work.'; stopped_pid=$scoringWatchPid; completed_prefix_tasks=@($scoringState.tasks).Count; creation_ticks=$scoringCreationTicks; identity_verified=$true} | ConvertTo-Json | Set-Content -LiteralPath 'D:/Code/CAE-Bench-OJ/runs/continuous-scoring/checkpoint-transition.json' -Encoding utf8
    Write-Output 'First15 complete; owned main stopped at checkpoint.'
    break
  }
  if ($null -eq (Get-CimInstance Win32_Process -Filter "ProcessId=$scoringWatchPid")) { throw 'Pack exited before the required checkpoint; inspect logs' }
  Start-Sleep -Milliseconds 300
}

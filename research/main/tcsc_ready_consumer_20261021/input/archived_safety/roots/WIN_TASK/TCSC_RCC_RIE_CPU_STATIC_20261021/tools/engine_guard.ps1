param([Parameter(Mandatory=$true)][string]$StatusPath,[Parameter(Mandatory=$true)][string]$RawPath,[Parameter(Mandatory=$true)][string]$StopPath,[Parameter(Mandatory=$true)][string]$AdapterLuid)
$ErrorActionPreference='Stop'
try {
 Get-Counter -Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -Continuous -ErrorAction Stop | ForEach-Object {
  if(Test-Path -LiteralPath $StopPath){exit 0}
  $valid=@($_.CounterSamples | Where-Object {$_.InstanceName -match 'pid_\d+_.*engtype_' -and $_.InstanceName -like "*_luid_${AdapterLuid}_phys_0_*"})
  if($valid.Count -eq 0){throw 'No PID-resolved GPU-engine counters'}
  if(@($valid | Where-Object {$_.Status -notin @(0,1)}).Count){throw 'Invalid GPU-engine counter status'}
  $positive=@($valid | Where-Object {$_.CookedValue -gt 0.001} | ForEach-Object {@{instance=$_.InstanceName;value=$_.CookedValue}})
  $obj=@{status='OK';utc=[DateTime]::UtcNow.ToString('o');epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();compute_counters=@($valid | Where-Object {$_.InstanceName -match 'engtype_(Compute|Cuda)'}).Count;all_counters=$valid.Count;positive=$positive;adapter_luid=$AdapterLuid;scope='ALL_NVIDIA_PID_RESOLVED_ENGINES_SHARED_3D_INCLUDED'}
  $json=$obj | ConvertTo-Json -Depth 6 -Compress
  Add-Content -LiteralPath $RawPath -Value $json -Encoding utf8
  $json | Set-Content -LiteralPath ($StatusPath+'.tmp') -Encoding utf8
  Move-Item -LiteralPath ($StatusPath+'.tmp') -Destination $StatusPath -Force
 }
} catch {
 @{status='ERROR';reason=$_.Exception.Message;epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()} | ConvertTo-Json -Compress | Set-Content -LiteralPath $StatusPath -Encoding utf8
 exit 1
}

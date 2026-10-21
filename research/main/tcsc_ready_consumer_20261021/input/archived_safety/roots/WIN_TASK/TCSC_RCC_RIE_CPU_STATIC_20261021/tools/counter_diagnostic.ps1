$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$out=Join-Path $root 'results\gpu_preflight\counter_native_diagnostic.json'
if(Test-Path -LiteralPath $out){throw 'Diagnostic already recorded'}
$errors=@()
$sets=Get-Counter -ListSet '*GPU*' -ErrorAction Continue -ErrorVariable +errors
$samples=Get-Counter -Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -MaxSamples 2 -ErrorAction Continue -ErrorVariable +errors
$all=@($samples.CounterSamples | Select-Object InstanceName,Status,CookedValue)
$nv=@($all | Where-Object {$_.InstanceName -like '*_luid_0x00000000_0x0000c82d_phys_0_*'})
@{purpose='Diagnose only; never grants execution';errors=@($errors | ForEach-Object {$_.Exception.Message});sets=@($sets | Select-Object CounterSetName,PathsWithInstances);nvidia_sample_count=$nv.Count;nvidia_status_groups=@($nv | Group-Object Status | Select-Object Name,Count);samples=$all} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $out -Encoding utf8
@{errors=@($errors | ForEach-Object {$_.Exception.Message});nvidia_sample_count=$nv.Count;nvidia_status_groups=@($nv | Group-Object Status | Select-Object Name,Count)} | ConvertTo-Json -Depth 6

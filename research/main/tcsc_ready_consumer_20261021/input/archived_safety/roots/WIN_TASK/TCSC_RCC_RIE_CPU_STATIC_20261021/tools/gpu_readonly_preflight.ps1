$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$dest=Join-Path $root 'results\gpu_preflight'
if(Test-Path -LiteralPath $dest){throw 'Read-only preflight already attempted; no automatic retry'}
New-Item -ItemType Directory -Path $dest | Out-Null
$result=@{cuda_children=0; status='UNKNOWN'; checks=@(); blockers=@()}
try {
 $smi='C:\Windows\System32\nvidia-smi.exe'
 & $smi -q -x 1> (Join-Path $dest 'native.xml') 2> (Join-Path $dest 'native.stderr.log')
 if($LASTEXITCODE -ne 0){throw 'nvidia-smi failed'}
 [xml]$xml=Get-Content -LiteralPath (Join-Path $dest 'native.xml') -Raw
 $gpus=@($xml.nvidia_smi_log.gpu)
 if($gpus.Count -ne 1){throw 'GPU inventory ambiguous'}
 $gpu=$gpus[0]
 $result.name=[string]$gpu.product_name
 $result.driver_model=[string]$gpu.driver_model.current_dm
 $result.free_memory=[string]$gpu.fb_memory_usage.free
 $result.temperature=[string]$gpu.temperature.gpu_temp
 $result.processes=@()
 foreach($item in @($gpu.processes.process_info)){
  if(-not $item){continue}
  $gpuPid=[int]$item.pid
  $identity=Get-CimInstance Win32_Process -Filter "ProcessId=$gpuPid"
  $p=@{pid=$gpuPid;type=[string]$item.type;name=[string]$item.process_name;module_status='UNKNOWN'}
  if(-not $identity){$result.blockers+= "Unresolved GPU PID $gpuPid"}
  else {
   $p.creation=$identity.CreationDate.ToUniversalTime().ToString('o')
   try {
    $modules=@((Get-Process -Id $gpuPid -ErrorAction Stop).Modules | ForEach-Object {$_.ModuleName})
    if($modules.Count -eq 0){throw 'Empty module list'}
    $p.compute_modules=@($modules | Where-Object {$_ -match '^(nvcuda|cudart|cublas|cudnn|cusparse|nvrtc|directml|torch|onnxruntime)'})
    $p.module_status='READ_OK'
    if($p.compute_modules.Count -gt 0){$result.blockers+="Compute-capable module loaded in PID $gpuPid"}
   }catch{$p.module_status=$_.Exception.Message;$result.blockers+="Module inventory unavailable PID $gpuPid"}
  }
  $result.processes+= $p
 }
 try {
  $samples=Get-Counter -Counter '\GPU Engine(*)\Utilization Percentage' -SampleInterval 1 -MaxSamples 2
  $samples | Export-Clixml -LiteralPath (Join-Path $dest 'engine_samples.xml')
  $valid=@($samples.CounterSamples | Where-Object {$_.InstanceName -match 'pid_\d+_.*engtype_' -and $_.Status -in @(0,1)})
  $result.engine_sample_count=$valid.Count
  $result.positive_engines=@($valid | Where-Object {$_.CookedValue -gt 0.001} | Select-Object InstanceName,CookedValue)
  if($valid.Count -eq 0){$result.blockers+='No PID-resolved engine counters'}
 }catch{$result.blockers+='GPU engine counters unavailable: '+$_.Exception.Message}
 if($result.name -notmatch 'RTX 4060 Ti'){$result.blockers+='Unexpected GPU'}
 if($result.free_memory -notmatch '^(\d+) MiB$'){$result.blockers+='VRAM telemetry unavailable'}elseif([int]$Matches[1] -lt 2048){$result.blockers+='Start VRAM below 2048 MiB'}
 if($result.temperature -notmatch '^(\d+) C$'){$result.blockers+='Temperature telemetry unavailable'}elseif([int]$Matches[1] -ge 78){$result.blockers+='Temperature >=78 C'}
 $result.status=if($result.blockers.Count){'BLOCKED_NO_GPU_LAUNCH'}else{'READONLY_INVENTORY_OK_CONTINUOUS_GUARD_STILL_REQUIRED'}
}catch{$result.status='BLOCKED_NO_GPU_LAUNCH';$result.blockers+=$_.Exception.Message}
$result | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $dest 'result.json') -Encoding utf8
$result | ConvertTo-Json -Depth 8

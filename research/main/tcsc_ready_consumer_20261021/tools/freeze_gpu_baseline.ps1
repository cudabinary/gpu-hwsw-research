$ErrorActionPreference='Stop'
$root=Split-Path -Parent $PSScriptRoot
$target=Join-Path $root 'config\GPU_FIXED_BASELINE.json'
if(Test-Path -LiteralPath $target){throw 'Baseline already frozen'}
$smi='C:\Windows\System32\nvidia-smi.exe'
[xml]$x=(& $smi -q -x)
if($LASTEXITCODE -ne 0){throw 'SMI unavailable'}
$gpu=@($x.nvidia_smi_log.gpu)
if($gpu.Count -ne 1){throw 'Ambiguous GPU'}
$luid=& (Join-Path $root 'build\adapter_luid.exe') | ConvertFrom-Json
if($LASTEXITCODE -ne 0){throw 'Adapter unavailable'}
$processes=@()
$prior=Get-Content -LiteralPath (Join-Path $root 'input\archived_safety\roots\WIN_TASK\TCSC_RCC_RIE_CPU_STATIC_20261021\config\GPU_FIXED_BASELINE.json') -Raw | ConvertFrom-Json
foreach($p in @($gpu[0].processes.process_info)){
 if(-not $p){continue}
 $item=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.pid)"
 if(-not $item){throw "GPU PID identity unavailable $($p.pid)"}
 $status='REQUIRES_NATIVE_SCAN'
 # Preserve the exact previously approved protected DWM identity, not a new
 # wildcard or a broad name-based exception. Native inventory is still required
 # for every ordinary GUI application.
 $known=@($prior.processes | Where-Object {$_.pid -eq [int]$p.pid -and $_.module_status -like 'PROTECTED_DWM_*'})
 if($known.Count -eq 1 -and $item.Name -eq 'dwm.exe'){
  $creation=if($known[0].creation -is [DateTime]){$known[0].creation}else{[DateTime]::Parse($known[0].creation)}
  if($creation.ToUniversalTime() -eq $item.CreationDate.ToUniversalTime()){$status=$known[0].module_status}
 }
 $processes+=@{pid=[int]$p.pid;creation=$item.CreationDate.ToUniversalTime().ToString('o');name=$item.Name;path=$item.ExecutablePath;module_status=$status}
}
# OS graphics brokers are identified by PID, name and creation time and never
# treated as arbitrary regular application exceptions.
$os=@()
foreach($item in @(Get-CimInstance Win32_Process | Where-Object {$_.Name -in @('System','csrss.exe')})){
 $os+=@{pid=[int]$item.ProcessId;creation=$item.CreationDate.ToUniversalTime().ToString('o');name=$item.Name;module_status='PROTECTED_OS_GRAPHICS_BROKER_CIM_IDENTITY'}
}
$native=& (Join-Path $root 'build\process_guard.exe') @($processes | Where-Object {$_.module_status -notlike 'PROTECTED_*'} | ForEach-Object {[string]$_.pid})
if($LASTEXITCODE -ne 0){throw "Native module inventory rejected: $native"}
$native | Set-Content -LiteralPath (Join-Path $root 'results\gpu_preflight\native_baseline_modules.json') -Encoding utf8
@{adapter_luid=$luid.luid;processes=$processes;engine_only_os_processes=$os;created_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $target -Encoding utf8
Write-Output "BASELINE_FROZEN regular=$($processes.Count) os=$($os.Count)"

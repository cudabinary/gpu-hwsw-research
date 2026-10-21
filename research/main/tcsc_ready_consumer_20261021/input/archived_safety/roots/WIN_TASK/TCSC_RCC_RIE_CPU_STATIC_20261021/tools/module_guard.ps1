param([Parameter(Mandatory=$true)][string]$BaselinePath,[Parameter(Mandatory=$true)][string]$StatusPath,[Parameter(Mandatory=$true)][string]$RawPath,[Parameter(Mandatory=$true)][string]$StopPath)
$ErrorActionPreference='Stop'
$baseline=Get-Content -LiteralPath $BaselinePath -Raw | ConvertFrom-Json
try {
 while(-not (Test-Path -LiteralPath $StopPath)){
  $checked=@();$absent=@()
  $regular=@($baseline.processes | Where-Object {$_.module_status -notlike 'PROTECTED_*'})
  $pidsToCheck=@($regular | ForEach-Object {[string]$_.pid})
  $native=(& "$PSScriptRoot\..\build\process_guard.exe" @pidsToCheck | ConvertFrom-Json)
  if($LASTEXITCODE -ne 0 -or $native.status -ne 'OK'){throw 'Native module inventory failed'}
  foreach($known in $regular){
   $actual=@($native.checked | Where-Object {$_.pid -eq $known.pid})
   if($actual.Count -eq 0){$absent+=@([int]$known.pid);continue}
   $expected=if($known.creation -is [DateTime]){$known.creation.ToUniversalTime()}else{[DateTime]::Parse($known.creation).ToUniversalTime()}
   if([Math]::Abs([long]$actual[0].creation_filetime-$expected.ToFileTimeUtc()) -gt 10){throw "PID identity changed $($known.pid)"}
   $checked+=@([int]$known.pid)
  }
  foreach($known in (@($baseline.processes)+@($baseline.engine_only_os_processes) | Where-Object {$_.module_status -like 'PROTECTED_*'})){
    $expected=if($known.creation -is [DateTime]){$known.creation.ToUniversalTime()}else{[DateTime]::Parse($known.creation).ToUniversalTime()}
    $identity=Get-CimInstance Win32_Process -Filter "ProcessId=$($known.pid)"
    if(-not $identity -or $identity.Name -ne $known.name -or $identity.CreationDate.ToUniversalTime() -ne $expected){throw 'Protected OS graphics identity changed'}
    $checked+=@([int]$known.pid)
  }
  $obj=@{status='OK';epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds();checked_pids=$checked;absent_pids=$absent}
  $json=$obj | ConvertTo-Json -Depth 4 -Compress
  Add-Content -LiteralPath $RawPath -Value $json -Encoding utf8
  $json | Set-Content -LiteralPath ($StatusPath+'.tmp') -Encoding utf8
  Move-Item -LiteralPath ($StatusPath+'.tmp') -Destination $StatusPath -Force
  Start-Sleep -Milliseconds 300
 }
}catch{
 @{status='ERROR';reason=$_.Exception.Message;epoch_ms=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()} | ConvertTo-Json -Compress | Set-Content -LiteralPath $StatusPath -Encoding utf8
 exit 1
}

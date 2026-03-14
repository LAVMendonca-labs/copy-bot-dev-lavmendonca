$processes = Get-CimInstance Win32_Process | Where-Object {
  $_.CommandLine -like '*run_copy_bot_live.py*'
}

foreach ($process in $processes) {
  Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
}

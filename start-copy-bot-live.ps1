param(
  [string]$HostName = "127.0.0.1",
  [int]$Port = 8875,
  [int]$RefreshSeconds = 20,
  [int]$ActivityLimit = 200,
  [int]$PositionsLimit = 200
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

python .\run_copy_bot_live.py `
  --host $HostName `
  --port $Port `
  --refresh-seconds $RefreshSeconds `
  --activity-limit $ActivityLimit `
  --positions-limit $PositionsLimit

<# --------------------------------------------------------------
   stop_friday.ps1
   Cleanly terminates the processes started by launch_friday.ps1
   -------------------------------------------------------------- #>

$base = Split-Path $MyInvocation.MyCommand.Path -Parent
$backendPidFile = Join-Path $base "backend.pid"
$frontendPidFile = Join-Path $base "frontend.pid"

function Stop-ProcessTree([int]$processId) {
    # Kill a process and all its descendants (uvicorn/npm spawn child processes).
    if (-not (Get-Process -Id $processId -ErrorAction SilentlyContinue)) { return }
    $children = Get-CimInstance Win32_Process |
        Where-Object { $_.ParentProcessId -eq $processId }
    foreach ($child in $children) { Stop-ProcessTree -processId $child.ProcessId }
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
}

function Kill-IfExists([string]$pidFile, [string]$name) {
    if (Test-Path $pidFile) {
        $pid = Get-Content $pidFile
        if (Get-Process -Id $pid -ErrorAction SilentlyContinue) {
            Write-Host "Stopping $name (PID $pid) and child processes ..."
            Stop-ProcessTree -processId $pid
        } else {
            Write-Host "$name PID file exists but process is already gone."
        }
        Remove-Item $pidFile -Force
    } else {
        Write-Host "$name PID file not found – nothing to stop."
    }
}

Kill-IfExists $frontendPidFile "frontend"
Kill-IfExists $backendPidFile  "backend"

Write-Host "✅ All Friday processes stopped."
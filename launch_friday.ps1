<# --------------------------------------------------------------
   launch_friday.ps1
   Robust launcher for the Friday project (Windows PowerShell)
   --------------------------------------------------------------
   Features
   • Checks for Python, Node, pip & npm
   • Installs missing dependencies (optional –install flag)
   • Loads .env variables into the session
   • Starts backend (FastAPI) with uvicorn
   • Waits for backend health (default 30 s timeout)
   • Starts the Next.js frontend only after a healthy backend
   • Writes PID files so the stop script can cleanly kill both
   • Clear status messages and graceful error handling
   -------------------------------------------------------------- #>

param(
    [switch]$Install,          # Run `pip install -r requirements.txt` and `npm install`
    [int]   $BackendPort = 8000,
    [int]   $HealthTimeout = 30,
    [switch]$NoFrontend        # Useful for API‑only testing
)

# ── Helper functions ────────────────────────────────────────
function Write-Info  { param($msg) Write-Host "[INFO]  $msg" -ForegroundColor Cyan }
function Write-Error { param($msg) Write-Host "[ERROR] $msg" -ForegroundColor Red }
function Write-Warn  { param($msg) Write-Host "[WARN]  $msg" -ForegroundColor Yellow }

# ── 1️⃣ Verify prerequisites ─────────────────────────────────
Write-Info "Verifying required tools..."

# Python
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found in PATH. Install Python 3.8+ and restart the terminal."
    exit 1
}
# Node
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Error "Node.js not found in PATH. Install Node >=16 and restart the terminal."
    exit 1
}

# ── 2️⃣ Load .env (if present) ─────────────────────────────────
$envFile = Join-Path $PSScriptRoot ".env"
if (Test-Path $envFile) {
    Write-Info "Loading environment variables from .env ..."
    Get-Content $envFile | ForEach-Object {
        if ($_ -match '^\s*#') { return }                 # skip comments
        if ($_ -match '^\s*$') { return }                # skip blank lines
        if ($_ -match '^\s*([^=]+)=(.*)$') {
            $name  = $matches[1].Trim()
            $value = $matches[2].Trim()
            $expanded = [Environment]::ExpandEnvironmentVariables($value)
            Set-Item -Path "Env:$name" -Value $expanded
        }
    }
} else {
    Write-Warn ".env file not found – proceeding with whatever env vars exist."
}

# ── 3️⃣ Optional dependency install ─────────────────────────────
if ($Install) {
    Write-Info "Installing Python requirements ..."
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { Write-Error "pip install failed."; exit 1 }

    Write-Info "Installing Node dependencies ..."
    Push-Location "$PSScriptRoot\frontend"
    npm install
    if ($LASTEXITCODE -ne 0) { Write-Error "npm install failed."; Pop-Location; exit 1 }
    Pop-Location
}

# ── 4️⃣ Start backend (uvicorn) ─────────────────────────────────
$backendLog  = Join-Path $PSScriptRoot "backend.log"
$backendPid  = Join-Path $PSScriptRoot "backend.pid"

Write-Info "Launching backend (uvicorn) on http://127.0.0.1:$BackendPort ..."
$uvicornArgs = @(
    "src.friday.api.main:app"
    "--host" "127.0.0.1"
    "--port" $BackendPort
)
$backendProc = Start-Process `
    -FilePath "python" `
    -ArgumentList @("-m","uvicorn") + $uvicornArgs `
    -RedirectStandardOutput $backendLog `
    -RedirectStandardError  $backendLog `
    -NoNewWindow `
    -PassThru

$backendProc.Id | Set-Content -Path $backendPid

Write-Info "✅ Backend launched (PID $($backendProc.Id))."

# ── 5️⃣ Wait for backend health ─────────────────────────────────
function Test-BackendHealthy {
    param([int]$port, [int]$timeoutSec)
    $end = (Get-Date).AddSeconds($timeoutSec)
    while ((Get-Date) -lt $end) {
        try {
            $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$port/health" `
                -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) { return $true }
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    return $false
}

Write-Info "Waiting for backend health (timeout $HealthTimeout s) ..."
if (-not (Test-BackendHealthy -port $BackendPort -timeoutSec $HealthTimeout)) {
    Write-Error "Backend did not become healthy within $HealthTimeout seconds. Check $backendLog"
    # Clean up the stray process
    if (Test-Path $backendPid) {
        $pid = Get-Content $backendPid
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
    }
    exit 1
}
Write-Info "✅ Backend is healthy!"

# ── 6️⃣ Start frontend (Next.js) ─────────────────────────────────
if (-not $NoFrontend) {
    $frontendLog = Join-Path $PSScriptRoot "frontend.log"
    $frontendPid = Join-Path $PSScriptRoot "frontend.pid"

    Write-Info "Launching Next.js frontend ..."
    Push-Location "$PSScriptRoot\frontend"
    $frontend = Start-Process `
        -FilePath "npm" `
        -ArgumentList "run","dev" `
        -RedirectStandardOutput $frontendLog `
        -RedirectStandardError  $frontendLog `
        -NoNewWindow `
        -PassThru
    $frontend.Id | Set-Content -Path $frontendPid
    Pop-Location

    Write-Info "🚀 All systems go!  Backend: http://127.0.0.1:$BackendPort   Frontend: http://localhost:3000"
    Write-Info "Logs: backend.log  frontend.log"
} else {
    Write-Info "🚀 Backend only – no frontend started (as requested)."
}
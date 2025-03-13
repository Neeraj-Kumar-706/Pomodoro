$ErrorActionPreference = "Stop"

# Setup paths
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
$VENV_PATH = Join-Path $INSTALL_DIR "venv"
$APP_PATH = Join-Path $INSTALL_DIR "app-v3.py"

# Verify installation
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "Error: App not installed."
    exit 1
}

try {
    # Change to installation directory
    Set-Location $INSTALL_DIR
    
    # Activate virtual environment and run app
    & "$VENV_PATH\Scripts\Activate.ps1"
    & "$VENV_PATH\Scripts\pythonw.exe" "$APP_PATH"
}
catch {
    Write-Host "Error launching app: $_"
    exit 1
}

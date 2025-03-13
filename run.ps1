$ErrorActionPreference = "Stop"

# Match install script paths
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
$VENV_PATH = Join-Path $INSTALL_DIR "venv"
$APP_PATH = Join-Path $INSTALL_DIR "draft.py"

# Verify installation
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "Error: App not installed"
    exit 1
}

try {
    Push-Location $INSTALL_DIR
    & "$VENV_PATH\Scripts\Activate.ps1"
    
    # Launch app using pythonw from venv
    Start-Process -NoNewWindow -FilePath "$VENV_PATH\Scripts\pythonw.exe" -ArgumentList $APP_PATH
}
catch {
    Write-Host "Error launching app: $_"
    exit 1
}
finally {
    Pop-Location
}

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
if (-not (Test-Path $APP_PATH)) {
    Write-Host "Error: App file missing."
    exit 1
}
if (-not (Test-Path "$VENV_PATH\Scripts\pythonw.exe")) {
    Write-Host "Error: Python environment not found."
    exit 1
}

try {
    # Change to installation directory
    Set-Location $INSTALL_DIR
    
    # Start app without console window
    Start-Process -WindowStyle Hidden `
                 -FilePath "$VENV_PATH\Scripts\pythonw.exe" `
                 -ArgumentList "$APP_PATH" `
                 -WorkingDirectory $INSTALL_DIR
}
catch {
    Write-Host "Error launching app: $_"
    exit 1
}

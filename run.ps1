$ErrorActionPreference = "Stop"

$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
$VENV_PATH = Join-Path $INSTALL_DIR "venv"
$APP_PATH = Join-Path $INSTALL_DIR "app-v3.py"

# Verify installation
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "Error: App not installed"
    exit 1
}

# Check for rain sound configuration
if (Test-Path "$INSTALL_DIR\rain_sound_path.txt") {
    $rainSoundPath = Get-Content "$INSTALL_DIR\rain_sound_path.txt"
    if (-not (Test-Path $rainSoundPath)) {
        Write-Host "Warning: Configured rain sound file not found"
    }
}

try {
    Push-Location $INSTALL_DIR
    & "$VENV_PATH\Scripts\Activate.ps1"
    Start-Process -NoNewWindow -FilePath "$VENV_PATH\Scripts\pythonw.exe" -ArgumentList $APP_PATH
}
catch {
    Write-Host "Error launching app: $_"
    exit 1
}
finally {
    Pop-Location
}

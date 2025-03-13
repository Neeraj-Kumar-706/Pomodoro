# Get the installation directory
$INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"

# Check if installation exists
if (-not (Test-Path $INSTALL_DIR)) {
    Write-Host "Pomodoro Timer is not installed. Please run the installer first."
    exit 1
}

# Change to installation directory
Set-Location $INSTALL_DIR

# Check virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Virtual environment not found. Please reinstall the application."
    exit 1
}

try {
    # Activate virtual environment and run app
    & ".\venv\Scripts\Activate.ps1"
    Start-Process -NoNewWindow -FilePath "pythonw.exe" -ArgumentList "app-v3.py"
}
catch {
    Write-Host "Error running application: $_"
    exit 1
}
finally {
    # Deactivate venv (PowerShell handles this automatically)
    exit 0
}

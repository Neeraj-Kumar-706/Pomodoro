# Enhanced PowerShell uninstallation script

$ErrorActionPreference = "Stop"

try {
    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
    $SHORTCUT = Join-Path ([Environment]::GetFolderPath("Desktop")) "PomodoroTimer.lnk"

    # Backup configuration files
    if (Test-Path "$INSTALL_DIR\rain_sound_path.txt") {
        Write-Host "Backing up rain sound configuration..."
        Copy-Item "$INSTALL_DIR\rain_sound_path.txt" "$env:TEMP\rain_sound_path.txt.bak"
    }

    # Backup settings
    if (Test-Path "$INSTALL_DIR\settings.json") {
        Write-Host "Backing up settings..."
        Copy-Item "$INSTALL_DIR\settings.json" "$env:TEMP\pomodoro_settings.json.bak"
    }

    # Create backup before removing
    if (Test-Path $INSTALL_DIR) {
        $backupDir = "${INSTALL_DIR}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Host "Creating backup at: $backupDir"
        Copy-Item -Path $INSTALL_DIR -Destination $backupDir -Recurse
        
        Write-Host "Removing installation directory..."
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
        Write-Host "Removed app files from: $INSTALL_DIR"
    }

    # Kill any running instances
    Get-Process | Where-Object {$_.Path -like "*PomodoroTimer*"} | Stop-Process -Force

    # Deactivate venv if active
    if ($env:VIRTUAL_ENV) {
        deactivate
    }

    # Remove installation with venv
    if (Test-Path "$INSTALL_DIR\venv") {
        Remove-Item -Path "$INSTALL_DIR\venv" -Recurse -Force
        Write-Host "Removed virtual environment"
    }

    # Remove shortcut if exists
    if (Test-Path $SHORTCUT) {
        Remove-Item -Path $SHORTCUT -Force
        Write-Host "Removed desktop shortcut"
    }

    # Remove Windows Registry entry
    Remove-Item "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\App Paths\PomodoroTimer.exe" -Force -ErrorAction SilentlyContinue

    Write-Host "Uninstallation complete!"
    Write-Host "Backup available at: $backupDir"
}
catch {
    Write-Host "Uninstallation failed: $_"
    exit 1
}

# Enhanced PowerShell uninstallation script

$ErrorActionPreference = "Stop"

try {
    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
    $SHORTCUT = Join-Path ([Environment]::GetFolderPath("Desktop")) "PomodoroTimer.lnk"
    $BACKUP_DIR = Join-Path $env:USERPROFILE ".config\pomodoro_backups"

    # Backup only settings
    if (Test-Path "$INSTALL_DIR\settings.json") {
        New-Item -ItemType Directory -Force -Path $BACKUP_DIR | Out-Null
        $backupFile = Join-Path $BACKUP_DIR "settings_$(Get-Date -Format 'yyyyMMdd_HHmmss').json"
        Copy-Item "$INSTALL_DIR\settings.json" $backupFile
        Write-Host "Settings backed up to: $backupFile"
    }

    # Kill running instances
    Get-Process | Where-Object {$_.Path -like "*app-v3.py*" -or $_.Path -like "*PomodoroTimer*"} | Stop-Process -Force
    Start-Sleep -Seconds 1  # Wait for processes to close

    # Remove installation
    if (Test-Path $INSTALL_DIR) {
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
        Write-Host "Removed app files from: $INSTALL_DIR"
    }

    # Remove shortcut and registry entry
    Remove-Item -Path $SHORTCUT -Force -ErrorAction SilentlyContinue
    Remove-Item "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\App Paths\PomodoroTimer.exe" -Force -ErrorAction SilentlyContinue

    Write-Host "Uninstallation complete!"
}
catch {
    Write-Host "Uninstallation failed: $_"
    exit 1
}

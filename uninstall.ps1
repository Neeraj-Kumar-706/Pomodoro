# Enhanced PowerShell uninstallation script

$ErrorActionPreference = "Stop"

try {
    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
    $SHORTCUT = Join-Path ([Environment]::GetFolderPath("Desktop")) "PomodoroTimer.lnk"

    # Create backup before removing
    if (Test-Path $INSTALL_DIR) {
        $backupDir = "${INSTALL_DIR}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Host "Creating backup at: $backupDir"
        Copy-Item -Path $INSTALL_DIR -Destination $backupDir -Recurse
        
        Write-Host "Removing installation directory..."
        Remove-Item -Path $INSTALL_DIR -Recurse -Force
        Write-Host "Removed app files from: $INSTALL_DIR"
    }

    # Remove shortcut if exists
    if (Test-Path $SHORTCUT) {
        Remove-Item -Path $SHORTCUT -Force
        Write-Host "Removed desktop shortcut"
    }

    Write-Host "Uninstallation complete!"
    Write-Host "Backup available at: $backupDir"
}
catch {
    Write-Host "Uninstallation failed: $_"
    exit 1
}

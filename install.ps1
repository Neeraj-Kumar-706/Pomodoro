# Enhanced PowerShell installation script

# Error handling
$ErrorActionPreference = "Stop"

function Backup-ExistingInstall {
    param($InstallPath)
    if (Test-Path $InstallPath) {
        $backupPath = "${InstallPath}_backup_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
        Write-Host "Backing up existing installation to $backupPath"
        Move-Item -Path $InstallPath -Destination $backupPath
    }
}

function Check-Python {
    try {
        $version = python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ([version]$version -lt [version]"3.8") {
            Write-Host "Python 3.8 or higher is required (found $version)"
            return $false
        }
        return $true
    }
    catch {
        Write-Host "Python is not installed"
        return $false
    }
}

function Install-Dependencies {
    try {
        Write-Host "Installing Python dependencies..."
        python -m pip install --user ttkbootstrap pygame matplotlib chime
        if ($LASTEXITCODE -ne 0) { throw "Pip install failed" }
    }
    catch {
        Write-Host "Failed to install dependencies: $_"
        return $false
    }
    return $true
}

# Main installation
try {
    if (-not (Check-Python)) {
        exit 1
    }

    # Verify source files
    if (-not (Test-Path "app-v3.py") -or -not (Test-Path "assets")) {
        Write-Host "Error: Required files not found. Make sure you're in the correct directory."
        exit 1
    }

    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
    Backup-ExistingInstall $INSTALL_DIR

    # Create and prepare installation directory
    New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

    if (-not (Install-Dependencies)) {
        exit 1
    }

    # Copy files with verification
    Write-Host "Copying application files..."
    Copy-Item "app-v3.py" -Destination $INSTALL_DIR -Force
    Copy-Item "assets" -Destination $INSTALL_DIR -Recurse -Force

    # Create and activate virtual environment
    Write-Host "Creating virtual environment..."
    python -m venv "$INSTALL_DIR\venv"
    
    # Install dependencies from requirements.txt
    Write-Host "Installing dependencies..."
    & "$INSTALL_DIR\venv\Scripts\pip" install ttkbootstrap pygame matplotlib chime
    if (Test-Path "requirements.txt") {
        & "$INSTALL_DIR\venv\Scripts\pip" install -r requirements.txt
    }

    # Create run script
    $runScript = @"
@echo off
call "$INSTALL_DIR\venv\Scripts\activate.bat"
python "$INSTALL_DIR\app-v3.py"
"@
    Set-Content -Path "$INSTALL_DIR\run.ps1" -Value $runScript

    # Create shortcut with error handling
    try {
        $WshShell = New-Object -comObject WScript.Shell
        $Shortcut = $WshShell.CreateShortcut("$Home\Desktop\PomodoroTimer.lnk")
        $Shortcut.TargetPath = "powershell.exe"
        $Shortcut.Arguments = "-ExecutionPolicy Bypass -File `"$INSTALL_DIR\run.ps1`""
        $Shortcut.WorkingDirectory = $INSTALL_DIR
        $Shortcut.Save()
    }
    catch {
        Write-Host "Warning: Failed to create desktop shortcut: $_"
    }

    Write-Host "Installation complete! App installed to: $INSTALL_DIR"
}
catch {
    Write-Host "Installation failed: $_"
    exit 1
}

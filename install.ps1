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
        if ([version]$version -ge [version]"3.8") {
            return $true  # Python version is good
        }
        Write-Host "Python 3.8 or higher is required (found $version)"
        return $false
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
    # Request admin rights if needed
    if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        Start-Process powershell.exe "-File",($MyInvocation.MyCommand.Path) -Verb RunAs
        exit
    }

    if (-not (Check-Python)) {
        exit 1
    }

    # Verify source files
    if (-not (Test-Path "draft.py") -or -not (Test-Path "assets")) {
        Write-Host "Error: Required files not found. Make sure you're in the correct directory."
        exit 1
    }

    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
    Backup-ExistingInstall $INSTALL_DIR

    # Store source directory
    $SOURCE_DIR = $PWD.Path

    # Create and prepare installation directory
    New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

    # Copy files first
    Write-Host "Copying application files..."
    Copy-Item "$SOURCE_DIR\draft.py" -Destination "$INSTALL_DIR\app-v3.py" -Force
    Copy-Item "$SOURCE_DIR\assets" -Destination $INSTALL_DIR -Recurse -Force

    # Create and activate virtual environment
    Write-Host "Creating virtual environment..."
    Push-Location $INSTALL_DIR
    python -m venv venv
    
    # Install dependencies
    Write-Host "Installing dependencies..."
    & ".\venv\Scripts\pip" install ttkbootstrap pygame matplotlib chime
    if (Test-Path "requirements.txt") {
        & ".\venv\Scripts\pip" install -r requirements.txt
    }
    Pop-Location

    # Ask for rain sound file
    $rainSoundPath = Read-Host "Enter path to rain sound MP3 file (or press Enter to skip)"
    
    if ($rainSoundPath) {
        if (Test-Path $rainSoundPath) {
            # Test if file is playable
            try {
                $testResult = python -c "import pygame; pygame.mixer.init(); pygame.mixer.music.load('$rainSoundPath')"
                Set-Content -Path "$INSTALL_DIR\rain_sound_path.txt" -Value $rainSoundPath
                Write-Host "Rain sound configured successfully"
            }
            catch {
                Write-Host "Warning: Sound file test failed, rain sound feature will be disabled"
            }
        }
        else {
            Write-Host "Warning: Invalid sound file, rain sound feature will be disabled"
        }
    }
    else {
        Write-Host "Rain sound feature will be disabled"
    }

    # Create initial settings.json
    $settings = @{
        pomodoro = 25
        short_break = 5
        long_break = 15
        mega_goal = 4
        auto_switch = $true
        sound_enabled = $true
        rain_sound_path = ""
    }
    $settings | ConvertTo-Json | Set-Content "$INSTALL_DIR\settings.json"

    # Create run script
    $runScript = @"
@echo off
call "$INSTALL_DIR\venv\Scripts\activate.bat"
python "$INSTALL_DIR\app-v3.py"
"@
    Set-Content -Path "$INSTALL_DIR\run.ps1" -Value $runScript

    # Create proper Windows shortcut
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$Home\Desktop\PomodoroTimer.lnk")
    $Shortcut.TargetPath = "$INSTALL_DIR\venv\Scripts\pythonw.exe"
    $Shortcut.Arguments = """$INSTALL_DIR\app-v3.py"""
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.IconLocation = "$INSTALL_DIR\assets\time-organization.ico"
    $Shortcut.Save()

    # Register in Windows Apps
    $AppPath = "Registry::HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\App Paths\PomodoroTimer.exe"
    New-Item -Path $AppPath -Force | Out-Null
    Set-ItemProperty -Path $AppPath -Name "(Default)" -Value "$INSTALL_DIR\venv\Scripts\pythonw.exe"
    Set-ItemProperty -Path $AppPath -Name "Path" -Value $INSTALL_DIR

    Write-Host "Installation complete! App installed to: $INSTALL_DIR"
}
catch {
    Write-Host "Installation failed: $_"
    exit 1
}

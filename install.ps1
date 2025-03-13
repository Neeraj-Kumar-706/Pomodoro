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

    # Verify Python first
    if (-not (Check-Python)) {
        Write-Host "Python check failed. Installation aborted."
        exit 1
    }

    # Store source directory and verify files
    $SOURCE_DIR = $PWD.Path
    if (-not (Test-Path "$SOURCE_DIR\draft.py") -or -not (Test-Path "$SOURCE_DIR\assets")) {
        Write-Host "Error: Required files not found. Make sure you're in the correct directory."
        exit 1
    }

    # Setup installation directory
    $INSTALL_DIR = Join-Path $env:LOCALAPPDATA "PomodoroTimer"
    Backup-ExistingInstall $INSTALL_DIR
    New-Item -ItemType Directory -Force -Path $INSTALL_DIR | Out-Null

    # Create and setup virtual environment
    Write-Host "Setting up Python environment..."
    Push-Location $INSTALL_DIR
    python -m venv venv
    & ".\venv\Scripts\Activate.ps1"
    & ".\venv\Scripts\pip" install ttkbootstrap pygame matplotlib chime
    Pop-Location

    # Copy application files
    Write-Host "Installing application files..."
    Copy-Item "$SOURCE_DIR\draft.py" -Destination "$INSTALL_DIR\app-v3.py" -Force
    Copy-Item "$SOURCE_DIR\assets" -Destination "$INSTALL_DIR" -Recurse -Force

    # Create settings file
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

    # Create shortcut
    $WshShell = New-Object -comObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("$Home\Desktop\PomodoroTimer.lnk")
    $Shortcut.TargetPath = "$INSTALL_DIR\venv\Scripts\pythonw.exe"
    $Shortcut.Arguments = "$INSTALL_DIR\app-v3.py"
    $Shortcut.WorkingDirectory = $INSTALL_DIR
    $Shortcut.Save()

    Write-Host "Installation complete! You can find PomodoroTimer on your desktop."
}
catch {
    Write-Host "Installation failed: $_"
    exit 1
}

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "tools\project.ps1")

$iconPath = Join-Path $PSScriptRoot "assets\DesktopPark.ico"
$outputPath = Join-Path $PSScriptRoot "dist\$ProjectExeName.exe"
$versionInfoPath = Join-Path ([System.IO.Path]::GetTempPath()) `
    ("DesktopPark-version-" + [guid]::NewGuid() + ".txt")

if (-not (Test-Path $iconPath)) {
    throw "Missing $iconPath. Run: python tools\make_icon.py (needs Pillow)."
}

python -m pip install pyinstaller -r (Join-Path $PSScriptRoot "requirements.txt")
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller installation failed with exit code $LASTEXITCODE."
}

Write-Host "Building $ProjectName $ProjectVersion"
New-VersionInfoFile -Path $versionInfoPath

try {
    python -m PyInstaller --noconfirm --clean --onefile --windowed `
        --name $ProjectExeName `
        --icon $iconPath `
        --version-file $versionInfoPath `
        --exclude-module PySide6.QtQml `
        --exclude-module PySide6.QtQuick `
        --exclude-module PySide6.QtPdf `
        --exclude-module PySide6.QtWebEngineCore `
        --exclude-module tkinter `
        --add-data "assets\fonts;assets\fonts" `
        (Join-Path $PSScriptRoot "desktop_park.py")
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $outputPath)) {
        throw "Desktop Park build failed with exit code $LASTEXITCODE."
    }
}
finally {
    Remove-Item $versionInfoPath -Force -ErrorAction SilentlyContinue
}

Write-Host "Done: $outputPath"

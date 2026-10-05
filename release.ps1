param(
    [string]$Version,
    [switch]$SkipBuild,
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "tools\project.ps1")

# desktop_park.py owns the version. An explicit -Version (the tag, in CI) is
# only allowed to agree with it, so a tag can never ship an EXE stamped with
# a different number than the installer around it.
if (-not $Version) {
    $Version = $ProjectVersion
} elseif ($Version -ne $ProjectVersion) {
    throw ("Version mismatch: asked for $Version but desktop_park.py " +
           "declares $ProjectVersion. Bump __version__ and re-tag.")
}

$exePath = Join-Path $PSScriptRoot "dist\DesktopPark.exe"
$releaseDir = Join-Path $PSScriptRoot "dist\release"
$artifactName = "DesktopPark-v$Version-windows-x64"
$zipPath = Join-Path $releaseDir "$artifactName.zip"
$zipChecksumPath = "$zipPath.sha256"
$installerPath = Join-Path $releaseDir "DesktopPark-v$Version-Setup.exe"
$installerChecksumPath = "$installerPath.sha256"
# The optional Theme Pack: a .parkpack file (portable users import it) and
# its own small installer (for the installed app). Not part of the app itself.
$packPath = Join-Path $releaseDir "DesktopPark-ThemePack-v$Version.parkpack"
$packInstallerPath = Join-Path $releaseDir "DesktopPark-ThemePack-v$Version-Setup.exe"
$stageRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("DesktopPark-release-" + [guid]::NewGuid())
$stageApp = Join-Path $stageRoot $artifactName

if (-not $SkipBuild) {
    & (Join-Path $PSScriptRoot "build.ps1")
}
if (-not (Test-Path $exePath)) {
    throw "Packaged app not found. Run .\build.ps1 first or omit -SkipBuild."
}

New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
New-Item -ItemType Directory -Path $stageApp -Force | Out-Null

try {
    Copy-Item $exePath $stageApp
    New-Item -ItemType File -Path (Join-Path $stageApp "portable.flag") | Out-Null
    Copy-Item (Join-Path $PSScriptRoot "README.md") $stageApp
    Copy-Item (Join-Path $PSScriptRoot "LICENSE") $stageApp
    Copy-Item (Join-Path $PSScriptRoot "THIRD-PARTY-NOTICES.md") $stageApp

    Remove-Item $zipPath, $zipChecksumPath -Force -ErrorAction SilentlyContinue
    Compress-Archive -Path $stageApp -DestinationPath $zipPath -CompressionLevel Optimal

    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zipPath)
    try {
        $relativePaths = @($archive.Entries | ForEach-Object {
            $_.FullName -replace '^[^/\\]+[/\\]', ''
        })
        $required = @('DesktopPark.exe', 'portable.flag', 'README.md', 'LICENSE', 'THIRD-PARTY-NOTICES.md')
        $missing = $required | Where-Object { $_ -notin $relativePaths }
        if ($missing) {
            throw "Release is missing required files: $($missing -join ', ')"
        }
        $private = $relativePaths | Where-Object {
            ($_ -match '^(data|local)[/\\]') -or
            ($_ -match '(park\.json|\.bak|\.tmp)$')
        }
        if ($private) {
            throw "Release contains private runtime files: $($private -join ', ')"
        }
    }
    finally {
        $archive.Dispose()
    }

    $hash = (Get-FileHash $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content $zipChecksumPath "$hash  $([System.IO.Path]::GetFileName($zipPath))" -Encoding ascii

    Remove-Item $packPath, "$packPath.sha256" -Force -ErrorAction SilentlyContinue
    python (Join-Path $PSScriptRoot "tools\build_pack.py") $packPath
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $packPath)) {
        throw "Theme Pack build failed with exit code $LASTEXITCODE."
    }
    $hash = (Get-FileHash $packPath -Algorithm SHA256).Hash.ToLowerInvariant()
    Set-Content "$packPath.sha256" "$hash  $([System.IO.Path]::GetFileName($packPath))" -Encoding ascii

    if (-not $SkipInstaller) {
        $isccCandidates = @(
            (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source),
            (Join-Path ${env:ProgramFiles(x86)} "Inno Setup 6\ISCC.exe"),
            (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe")
        ) | Where-Object { $_ -and (Test-Path $_) }
        $iscc = $isccCandidates | Select-Object -First 1
        if (-not $iscc) {
            throw "Inno Setup 6 was not found. Install it or use -SkipInstaller."
        }

        Remove-Item $installerPath, $installerChecksumPath -Force -ErrorAction SilentlyContinue
        & $iscc "/DMyAppVersion=$Version" "/DMyAppPublisher=$ProjectPublisher" `
            "/DMyAppURL=$ProjectUrl" (Join-Path $PSScriptRoot "installer.iss")
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $installerPath)) {
            throw "Installer build failed with exit code $LASTEXITCODE."
        }
        $hash = (Get-FileHash $installerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        Set-Content $installerChecksumPath `
            "$hash  $([System.IO.Path]::GetFileName($installerPath))" -Encoding ascii

        Remove-Item $packInstallerPath, "$packInstallerPath.sha256" -Force -ErrorAction SilentlyContinue
        & $iscc "/DMyAppVersion=$Version" "/DMyAppPublisher=$ProjectPublisher" `
            "/DMyAppURL=$ProjectUrl" (Join-Path $PSScriptRoot "pack-installer.iss")
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $packInstallerPath)) {
            throw "Theme Pack installer build failed with exit code $LASTEXITCODE."
        }
        $hash = (Get-FileHash $packInstallerPath -Algorithm SHA256).Hash.ToLowerInvariant()
        Set-Content "$packInstallerPath.sha256" `
            "$hash  $([System.IO.Path]::GetFileName($packInstallerPath))" -Encoding ascii
    }
}
finally {
    Remove-Item $stageRoot -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Portable: $zipPath"
Write-Host "SHA-256: $zipChecksumPath"
Write-Host "Theme Pack: $packPath"
if (-not $SkipInstaller) {
    Write-Host "Installer: $installerPath"
    Write-Host "SHA-256: $installerChecksumPath"
    Write-Host "Theme Pack installer: $packInstallerPath"
}
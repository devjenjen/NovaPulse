# Build Script for NovaPulse v0.2.0

$ErrorActionPreference = "Stop"

# Ensure src/main.pyw exists
if (-not (Test-Path "src/main.pyw")) {
    Write-Error "Could not find src/main.pyw. Please run this script from the root of the repository."
    exit 1
}

Write-Host "Building NovaPulse Executable..." -ForegroundColor Cyan

# Install requirements
python -m pip install -r requirements.txt
python -m pip install pyinstaller

# Clean old builds
if (Test-Path "build") { Remove-Item "build" -Recurse -Force }
if (Test-Path "dist") { Remove-Item "dist" -Recurse -Force }

# Run PyInstaller
python -m PyInstaller --noconfirm --onefile --windowed --icon "assets/icon.ico" --name "NovaPulse" "src/main.pyw"

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed."
    exit 1
}

Write-Host "Build successful! Executable is located in dist/NovaPulse/" -ForegroundColor Green

# Flutter Asennus Windows - Automaattinen skripti
# Aja tämä PowerShell Admin-oikeuksilla

Write-Host "=== Flutter Asennus ===" -ForegroundColor Green

# 1. Lataa Flutter
$flutterZip = "$env:USERPROFILE\Downloads\flutter_windows.zip"
$flutterUrl = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.16.0-stable.zip"

Write-Host "Ladataan Flutter..." -ForegroundColor Yellow
Invoke-WebRequest -Uri $flutterUrl -OutFile $flutterZip

# 2. Pura Flutter
$flutterPath = "C:\src\flutter"
Write-Host "Puretaan Flutter kansioon $flutterPath..." -ForegroundColor Yellow
Expand-Archive -Path $flutterZip -DestinationPath "C:\src" -Force

# 3. Lisää PATH:iin
$flutterBin = "$flutterPath\bin"
Write-Host "Lisätään Flutter PATH:iin..." -ForegroundColor Yellow

# Hae nykyinen PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")

# Lisää Flutter jos ei ole jo
if ($currentPath -notlike "*$flutterBin*") {
    $newPath = "$currentPath;$flutterBin"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "✓ Flutter lisätty PATH:iin!" -ForegroundColor Green
} else {
    Write-Host "✓ Flutter on jo PATH:issa" -ForegroundColor Green
}

# 4. Päivitä nykyinen sessio
$env:Path = [Environment]::GetEnvironmentVariable("Path", "User")

# 5. Tarkista asennus
Write-Host "`nTarkistetaan asennus..." -ForegroundColor Yellow
flutter doctor

Write-Host "`n=== Asennus valmis! ===" -ForegroundColor Green
Write-Host "Käynnistä terminaali uudelleen ja aja: flutter doctor" -ForegroundColor Cyan

# Tämä skripti avaa portit 8000 ja 8081 Windowsin palomuurista
# Suorita järjestelmänvalvojan oikeuksilla (Run as Administrator)

Write-Host "Avataan portti 8000 (Pingut API)..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "Pingut API (8000)" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -Profile Any | Out-Null

Write-Host "Avataan portti 8081 (Open-Meteo Backend)..." -ForegroundColor Cyan
New-NetFirewallRule -DisplayName "Pingut Meteo (8081)" -Direction Inbound -LocalPort 8081 -Protocol TCP -Action Allow -Profile Any | Out-Null

Write-Host "Valmis! Portit 8000 ja 8081 on nyt avattu." -ForegroundColor Green
Write-Host "Paina ENTER lopettaaksesi."
Read-Host

# Run this after starting the API in another PowerShell window.
$base = "http://127.0.0.1:8000"
Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/api/messes"
Write-Host "Public endpoint smoke test finished."

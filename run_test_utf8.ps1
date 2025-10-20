# Quick Test Runner with Proper Encoding
# This script ensures proper UTF-8 encoding in PowerShell

# Set console to UTF-8
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$env:PYTHONIOENCODING = "utf-8"

Write-Host "Running test with proper UTF-8 encoding..." -ForegroundColor Green
Write-Host ""

# Run the test
python run_test.py test_urls.txt

Write-Host ""
Write-Host "Test complete!" -ForegroundColor Green

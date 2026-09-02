Param(
    [string]$TargetFolder,
    [string]$XRawStudioExe
)

# 2. Update the exact Registry Key and Property you found
$RegPath = "HKCU:\Software\COM.FUJIFILM.DEN\x_raw_studio_fujifilm"
Set-ItemProperty -Path $RegPath -Name "FolderPath" -Value $TargetFolder

Write-Host "Success: Updated X RAW Studio to load: $TargetFolder" -ForegroundColor Green

# 3. Launch the application
Start-Process $XRawStudioExe

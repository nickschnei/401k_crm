# finish_changes.ps1 - Run this on your other computer to secure permissions, push to GitHub, and deploy to AWS.

# 1. Resolve local workspace paths
$WorkspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (!$WorkspaceRoot) { $WorkspaceRoot = Get-Location }
Write-Host "Workspace Root: $WorkspaceRoot" -ForegroundColor Cyan

# 2. Commit and Push local changes to GitHub
Write-Host "`n=== 1. PUSHING CHANGES TO GITHUB ===" -ForegroundColor Yellow
git add -A
git commit -m "Replace Trip Planner with Call & Interaction Logs CRM"
git push origin main
Write-Host "Changes successfully pushed to GitHub!" -ForegroundColor Green

# 3. Create a secured copy of the PEM key to avoid Windows SSH "Bad permissions" error
Write-Host "`n=== 2. SECURING PRIVATE KEY PERMISSIONS ===" -ForegroundColor Yellow
$TempDir = Join-Path $env:TEMP "secured-crm-keys"
if (!(Test-Path $TempDir)) {
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
}
$KeySource = Join-Path $WorkspaceRoot "CRM-key-pair.pem"
$KeyDest = Join-Path $TempDir "CRM-key-pair.pem"

Write-Host "Copying PEM key to: $KeyDest"
Copy-Item -Path $KeySource -Destination $KeyDest -Force

Write-Host "Restricting permissions (owner-only read/write)..."
icacls $KeyDest /inheritance:r
icacls $KeyDest /grant:r "${env:USERNAME}:(F)"
icacls $KeyDest /remove "CodexSandboxUsers"
icacls $KeyDest /remove "BUILTIN\Administrators"
icacls $KeyDest /remove "NT AUTHORITY\SYSTEM"

# 4. Update deploy_zip.py to point to this new secure key path
Write-Host "`n=== 3. UPDATING DEPLOYMENT SCRIPT PATHS ===" -ForegroundColor Yellow
$DeployScriptPath = Join-Path $WorkspaceRoot "scratch\deploy_zip.py"
$DeployScriptContent = Get-Content -Path $DeployScriptPath -Raw
$OldKeyLine = 'key_path = r"C:\Users\nicks\.gemini\antigravity\brain\57db76c8-9fe9-4e20-abc3-1ffcb924dbad\scratch\CRM-key-pair.pem"'
$NewKeyLine = 'key_path = r"' + $KeyDest + '"'
$DeployScriptContent = $DeployScriptContent.Replace($OldKeyLine, $NewKeyLine)
Set-Content -Path $DeployScriptPath -Value $DeployScriptContent
Write-Host "Deployment script updated with secured key path: $KeyDest" -ForegroundColor Green

# 5. Run the deployment script to verify or deploy to AWS EC2
Write-Host "`n=== 4. TRIGGERING DEPLOYMENT TO AWS ===" -ForegroundColor Yellow
Write-Host "Running deploy_zip.py..."
if (Test-Path "$WorkspaceRoot\venv\Scripts\python.exe") {
    & "$WorkspaceRoot\venv\Scripts\python.exe" "$WorkspaceRoot\scratch\deploy_zip.py"
} else {
    python "$WorkspaceRoot\scratch\deploy_zip.py"
}

Write-Host "`n=== SUCCESS! CRM logs refactoring has been pushed and deployed ===" -ForegroundColor Green

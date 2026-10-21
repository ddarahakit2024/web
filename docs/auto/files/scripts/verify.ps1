# Done check: backend pytest + frontend Jest + build. Last line is VERIFY PASS or VERIFY FAIL.
# Usage: powershell -File scripts/verify.ps1
$ErrorActionPreference = 'Continue'
$Root = Split-Path -Parent $PSScriptRoot
if ($env:VERIFY_PYTHON) { $Python = $env:VERIFY_PYTHON }
elseif (Test-Path "$Root\.venv\Scripts\python.exe") { $Python = "$Root\.venv\Scripts\python.exe" }
else { $Python = 'python' }

function Step($Name, $Dir, [scriptblock]$Cmd) {
    Write-Host "== $Name"
    Push-Location $Dir
    & $Cmd
    $code = $LASTEXITCODE
    Pop-Location
    if ($code -ne 0) { Write-Host "VERIFY FAIL: $Name"; exit 1 }
}

Step 'pytest' $Root { & $Python -m pytest -q }
Step 'jest' "$Root\frontend" { npm test --silent }
Step 'build' "$Root\frontend" { npm run build }
Write-Host 'VERIFY PASS'

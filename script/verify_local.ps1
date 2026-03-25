$ErrorActionPreference = "Stop"

param(
    [switch]$Quick,
    [switch]$SkipBuild
)

$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $repoRoot

$logDir = Join-Path $repoRoot "artifacts/verify"
New-Item -Path $logDir -ItemType Directory -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$logFile = Join-Path $logDir "local-verify-$timestamp.log"
$resultDir = Join-Path $logDir "results-$timestamp"
New-Item -Path $resultDir -ItemType Directory -Force | Out-Null

function Write-Log {
    param([string]$Message)
    $line = "[{0}] {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    $line | Tee-Object -FilePath $logFile -Append
}

function Resolve-Python {
    $venvPython = Join-Path $repoRoot ".venv/Scripts/python.exe"
    if (Test-Path $venvPython) {
        return $venvPython
    }

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        return $pythonCmd.Source
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        return "$($pyCmd.Source) -3"
    }

    throw "Python runtime was not found. Create .venv or install Python and retry."
}

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Action
    )

    Write-Log "=== START: $Name ==="
    & $Action 2>&1 | Tee-Object -FilePath $logFile -Append
    $exitCode = $LASTEXITCODE
    if ($null -eq $exitCode) {
        $exitCode = 0
    }

    if ($exitCode -ne 0) {
        Write-Log "=== FAIL: $Name (exit $exitCode) ==="
        throw "$Name failed with exit code $exitCode"
    }

    Write-Log "=== PASS: $Name ==="
}

Write-Log "Local verification started. quick=$Quick skipBuild=$SkipBuild"

$pythonExec = Resolve-Python

if ($pythonExec -like "* *") {
    $pythonParts = $pythonExec.Split(" ", 2)
    $pythonCommand = $pythonParts[0]
    $pythonArgPrefix = $pythonParts[1]
} else {
    $pythonCommand = $pythonExec
    $pythonArgPrefix = ""
}

Invoke-Step "Architecture compliance tests" {
    if ($pythonArgPrefix) {
        & $pythonCommand $pythonArgPrefix -m pytest -q tests/functional/test_api_architecture_compliance.py --junitxml "$resultDir/architecture-compliance.xml"
    } else {
        & $pythonCommand -m pytest -q tests/functional/test_api_architecture_compliance.py --junitxml "$resultDir/architecture-compliance.xml"
    }
}

if (-not $Quick) {
    Invoke-Step "Document flow functional tests" {
        if ($pythonArgPrefix) {
            & $pythonCommand $pythonArgPrefix -m pytest -q tests/functional/test_api_documents.py tests/functional/test_api_confirmations.py tests/functional/test_api_documents_boundaries.py --junitxml "$resultDir/document-flows.xml"
        } else {
            & $pythonCommand -m pytest -q tests/functional/test_api_documents.py tests/functional/test_api_confirmations.py tests/functional/test_api_documents_boundaries.py --junitxml "$resultDir/document-flows.xml"
        }
    }
}

if (-not $SkipBuild) {
    Invoke-Step "Frontend/backend build" {
        npm run build
    }
}

Write-Log "Verification complete. Log file: $logFile"
Write-Log "JUnit reports directory: $resultDir"
Write-Output "VERIFY_LOG=$logFile"
Write-Output "VERIFY_RESULTS=$resultDir"

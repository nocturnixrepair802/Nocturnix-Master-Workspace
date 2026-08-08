$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

Write-Host "========================================"
Write-Host "Nocturnix AI Assistant environment setup"
Write-Host "========================================"

Write-Host "`nWorking directory:"
Get-Location

Write-Host "`nGit version:"
git --version
if ($LASTEXITCODE -ne 0) { throw 'Git is unavailable.' }

Write-Host "`nPython version:"
python --version
if ($LASTEXITCODE -ne 0) { throw 'Python is unavailable.' }

Write-Host "`nCreating virtual environment..."

if (-not (Test-Path -LiteralPath ".venv" -PathType Container)) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Virtual environment creation failed.' }
}

$pythonExecutable = Join-Path ".venv" "Scripts\python.exe"

if (-not (Test-Path -LiteralPath $pythonExecutable -PathType Leaf)) {
    throw "The virtual environment Python executable was not found at $pythonExecutable."
}

Write-Host "`nUpgrading Python packaging tools..."
& $pythonExecutable -m pip install --upgrade pip setuptools wheel
if ($LASTEXITCODE -ne 0) { throw 'Packaging tool upgrade failed.' }

Write-Host "`nInstalling project dependencies..."

if ((Test-Path -LiteralPath "pyproject.toml" -PathType Leaf) -and
    (Get-Item -LiteralPath "pyproject.toml").Length -gt 0) {
    & $pythonExecutable -m pip install -e ".[dev]"

    if ($LASTEXITCODE -ne 0) {
        Write-Host "The project does not define a dev extra; installing the base project."
        & $pythonExecutable -m pip install -e .
        if ($LASTEXITCODE -ne 0) { throw 'Project installation failed.' }
    }
}
elseif ((Test-Path -LiteralPath "requirements-dev.txt" -PathType Leaf) -and
        (Get-Item -LiteralPath "requirements-dev.txt").Length -gt 0) {
    & $pythonExecutable -m pip install -r requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'Development dependency installation failed.' }
}
elseif ((Test-Path -LiteralPath "requirements.txt" -PathType Leaf) -and
        (Get-Item -LiteralPath "requirements.txt").Length -gt 0) {
    & $pythonExecutable -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
else {
    Write-Host "No populated dependency file was found."
    Write-Host "Skipping dependency installation."
}

Write-Host "`nInstalled Python packages:"
& $pythonExecutable -m pip list
if ($LASTEXITCODE -ne 0) { throw 'Unable to list installed packages.' }

Write-Host "`nEnvironment setup complete."

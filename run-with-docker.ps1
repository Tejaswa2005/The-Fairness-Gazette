$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$backendEnvExample = Join-Path $root 'Backend\.env.example'
$backendEnv = Join-Path $root 'Backend\.env'
$frontendEnvExample = Join-Path $root 'frontend\.env.example'
$frontendEnv = Join-Path $root 'frontend\.env'

if (-not (Test-Path $backendEnv) -and (Test-Path $backendEnvExample)) {
    Copy-Item $backendEnvExample $backendEnv
}

if (-not (Test-Path $frontendEnv) -and (Test-Path $frontendEnvExample)) {
    Copy-Item $frontendEnvExample $frontendEnv
}

Write-Host 'Starting Docker Compose...'
Write-Host 'Frontend will be available at http://localhost:5173'
Write-Host 'Backend docs will be available at http://localhost:8000/docs'

docker compose up --build

# AgentFlow 一键部署 (Windows)
# 首次运行: 右键 -> 使用 PowerShell 运行，或在项目根目录执行 .\deploy.ps1
# 之后只需打开 Docker Desktop，所有服务会自动启动 (restart: unless-stopped)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "==> AgentFlow Docker 部署" -ForegroundColor Cyan

if (-not (Test-Path "api\.env")) {
    Copy-Item "api\.env.example" "api\.env"
    Write-Host "已创建 api\.env，请编辑 API Key 后重新运行。" -ForegroundColor Yellow
    exit 1
}

Write-Host "==> 构建并启动全部服务 (首次约 5-10 分钟)..." -ForegroundColor Cyan
docker compose up -d --build
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "==> 等待 API 就绪..." -ForegroundColor Cyan
$deadline = (Get-Date).AddMinutes(5)
while ((Get-Date) -lt $deadline) {
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 5
        if ($r.StatusCode -eq 200) { break }
    } catch {}
    Start-Sleep -Seconds 5
}

Write-Host ""
Write-Host "部署完成!" -ForegroundColor Green
Write-Host "  Web UI:  http://localhost"
Write-Host "  API:     http://localhost:8000/docs"
Write-Host "  账号:    admin / admin123  (首次启动自动创建)"
Write-Host ""
Write-Host "下次只需打开 Docker Desktop，无需再运行此脚本。" -ForegroundColor Yellow
docker compose ps

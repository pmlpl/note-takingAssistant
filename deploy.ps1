# NoteMind Docker 一键部署脚本 (PowerShell)
# 用法: 右键 -> 使用 PowerShell 运行，或在终端执行 .\deploy.ps1

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  NoteMind Docker 一键部署" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查 Docker
try {
    docker --version | Out-Null
} catch {
    Write-Host "[错误] 未检测到 Docker，请先安装 Docker Desktop" -ForegroundColor Red
    Write-Host "下载地址: https://www.docker.com/products/docker-desktop/"
    Read-Host "按回车键退出"
    exit 1
}

# 检查 Docker 是否运行
try {
    docker info | Out-Null
} catch {
    Write-Host "[错误] Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "[√] Docker 已就绪" -ForegroundColor Green
Write-Host ""

# 复制环境配置
Write-Host "[1/3] 检查环境配置..."
if (-not (Test-Path .env)) {
    Copy-Item .env.simple .env
    Write-Host "  已创建 .env 文件（使用默认配置）"
} else {
    Write-Host "  .env 已存在，跳过创建"
}
Write-Host ""

# 读取端口
$envContent = Get-Content .env
$port = "8080"
foreach ($line in $envContent) {
    if ($line -match "^EXTERNAL_PORT=(\d+)") {
        $port = $Matches[1]
    }
}

# 构建并启动
Write-Host "[2/3] 构建并启动容器..."
Write-Host "  首次构建需要 5-15 分钟，请耐心等待..."
Write-Host ""

docker compose -f docker-compose.simple.yml --env-file .env up -d --build

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[错误] 部署失败，请查看上方错误信息" -ForegroundColor Red
    Read-Host "按回车键退出"
    exit 1
}

Write-Host ""
Write-Host "[3/3] 等待服务初始化（约 15 秒）..."
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  部署完成！" -ForegroundColor Green
Write-Host "  访问地址: http://localhost:8090" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "常用命令:"
Write-Host "  查看日志: docker compose -f docker-compose.simple.yml logs -f"
Write-Host "  停止服务: docker compose -f docker-compose.simple.yml down"
Write-Host "  重启服务: docker compose -f docker-compose.simple.yml restart"
Write-Host "  查看状态: docker compose -f docker-compose.simple.yml ps"
Write-Host ""
Write-Host "提示: 首次打开页面如报错，请等待 30 秒后刷新（数据库初始化中）"
Write-Host ""

# 自动打开浏览器
Start-Process "http://localhost:8090"

Read-Host "按回车键退出"

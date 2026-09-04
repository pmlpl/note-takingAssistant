@echo off
chcp 65001 >nul
title NoteMind Docker 一键部署

echo ========================================
echo   NoteMind Docker 一键部署
echo ========================================
echo.

REM ---------- 检查 Docker ----------
docker --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到 Docker，请先安装 Docker Desktop
    echo 下载地址: https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

REM ---------- 检查 Docker 是否运行 ----------
docker info >nul 2>&1
if errorlevel 1 (
    echo [错误] Docker 未运行，请先启动 Docker Desktop
    echo.
    pause
    exit /b 1
)

echo [√] Docker 已就绪
echo.

REM ---------- 复制环境配置 ----------
echo [1/3] 检查环境配置...
if not exist .env (
    copy .env.simple .env >nul
    echo   已创建 .env 文件（使用默认配置）
) else (
    echo   .env 已存在，跳过创建
)
echo.

REM ---------- 构建并启动 ----------
echo [2/3] 构建并启动容器...
echo   首次构建需要 5-15 分钟，请耐心等待...
echo.

docker compose -f docker-compose.simple.yml --env-file .env up -d --build

if errorlevel 1 (
    echo.
    echo [错误] 部署失败，请查看上方错误信息
    echo.
    pause
    exit /b 1
)

echo.
echo [3/3] 等待服务初始化（约 15 秒）...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo   部署完成！
echo   访问地址: http://localhost:8090
echo ========================================
echo.
echo 常用命令:
echo   查看日志: docker compose -f docker-compose.simple.yml logs -f
echo   停止服务: docker compose -f docker-compose.simple.yml down
echo   重启服务: docker compose -f docker-compose.simple.yml restart
echo   查看状态: docker compose -f docker-compose.simple.yml ps
echo.
echo 提示: 首次打开页面如报错，请等待 30 秒后刷新（数据库初始化中）
echo.

REM 自动打开浏览器
start http://localhost:8090

pause

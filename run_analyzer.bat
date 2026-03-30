@echo off
chcp 936 >nul
title Video Analyzer Pro - Self-healing Runner

echo ==================================================
echo    视频识别分析器专业版 (Video Analyzer Pro)
echo ==================================================
echo.

rem 1. 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [状态] 发现系统未安装 Python，正在尝试自动安装...
    winget install -e --id Python.Python.3 --accept-source-agreements --accept-package-agreements
    if %errorlevel% neq 0 (
        echo [错误] 自动安装 Python 失败！请手动安装。
        pause
        exit
    )
    echo [提示] Python 安装成功！请重新启动本脚本。
    pause
    exit
)

rem 2. 检查 FFmpeg
where ffmpeg >nul 2>nul
if %errorlevel% neq 0 (
    echo [状态] 正在尝试部署系统级多媒体库...
    winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements >nul
    echo [提示] 如果部署失败，程序将自动使用 OpenCV 默认解码器运行。
)

rem 3. 运行环境同步
set "PROJECT_DIR=%~dp0"
cd /d "%PROJECT_DIR%"

echo [状态] 正在同步 Python 环境依赖库...
python -m pip install --upgrade pip --quiet --user
python -m pip install -r requirements.txt --quiet --user

echo [状态] 环境已就绪，正在启动主程序...
echo --------------------------------------------------
python main.py

echo.
echo --------------------------------------------------
echo 程序运行已结束。
pause

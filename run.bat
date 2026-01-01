@echo off
chcp 65001 >nul
echo ========================================
echo 会议翻译工具 - 启动中...
echo Meeting Translator - Starting...
echo ========================================
echo.

REM 检查 .env 文件是否存在
if not exist ".env" (
    echo [错误] 未找到 .env 配置文件
    echo [Error] .env configuration file not found
    echo.
    echo 请复制 .env.example 为 .env 并填入你的 API Key
    echo Please copy .env.example to .env and fill in your API Key
    echo.
    pause
    exit /b 1
)

REM 激活虚拟环境 (如果存在)
if exist ".venv\Scripts\activate.bat" (
    echo 使用虚拟环境...
    echo Using virtual environment...
    call .venv\Scripts\activate.bat
)

REM 检查是否安装了依赖
python -c "import PyQt5" 2>nul
if errorlevel 1 (
    echo.
    echo [错误] 未安装依赖包
    echo [Error] Dependencies not installed
    echo.
    echo 请运行: pip install -r requirements.txt
    echo Please run: pip install -r requirements.txt
    echo.
    pause
    exit /b 1
)

REM 运行程序
cd meeting_translator
python main_app.py
cd ..

if errorlevel 1 (
    echo.
    echo ========================================
    echo 错误：程序运行失败
    echo Error: Program failed to run
    echo ========================================
    echo.
    echo 请检查:
    echo Please check:
    echo 1. 是否已安装所有依赖: pip install -r requirements.txt
    echo    All dependencies installed: pip install -r requirements.txt
    echo 2. 是否已配置 .env 文件
    echo    .env file configured
    echo 3. 是否已安装 Voicemeeter
    echo    Voicemeeter installed
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo 程序已退出
echo Program exited
echo ========================================
pause

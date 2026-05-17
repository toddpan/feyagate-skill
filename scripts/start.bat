@echo off
setlocal enabledelayedexpansion
:: FeyaGate Skill — Start MCP Server (Windows)

set "ROOT=%~dp0.."
set "BIN=%ROOT%\bin\miloco-mcp-server.exe"
set "CONFIG=%ROOT%\config\config.yaml"
set "LOG=%ROOT%\data\miloco-mcp-server.log"
set "PORT=38080"

:: Read port from config.yaml
if exist "%CONFIG%" (
    for /f "tokens=2 delims=: " %%a in ('findstr /r "http_port:" "%CONFIG%"') do set "PORT=%%a"
)

if "%~1"=="--port" set "PORT=%~2"

if not exist "%BIN%" (
    echo ERROR: bin\miloco-mcp-server.exe not found
    echo Run: scripts\setup.bat
    exit /b 1
)

if not exist "%CONFIG%" (
    if exist "%ROOT%\config\config.yaml.example" (
        copy "%ROOT%\config\config.yaml.example" "%CONFIG%" >nul
    ) else (
        echo ERROR: config\config.yaml not found
        exit /b 1
    )
)

if not exist "%ROOT%\data" mkdir "%ROOT%\data"

:: Add lib\ to PATH for DLL loading
set "PATH=%ROOT%\lib;%PATH%"

echo Starting miloco-mcp-server (port %PORT%)...
cd /d "%ROOT%"
start /B "" "%BIN%" --config "%CONFIG%" > "%LOG%" 2>&1
timeout /t 2 /nobreak >nul

curl -s -o nul -w "%%{http_code}" "http://localhost:%PORT%/health" > "%ROOT%\data\_hc.tmp" 2>nul
set /p HC=<"%ROOT%\data\_hc.tmp"
del "%ROOT%\data\_hc.tmp" 2>nul

if "!HC!"=="200" (
    echo OK: http://localhost:%PORT%/mcp/http
) else (
    echo Started but health=!HC!
    echo Check: type data\miloco-mcp-server.log
)

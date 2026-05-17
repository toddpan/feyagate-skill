@echo off
setlocal enabledelayedexpansion
:: FeyaGate Skill — Verify installation (Windows)

set "ROOT=%~dp0.."
set ERRORS=0

echo === FeyaGate Skill — Verify ===
echo Root: %ROOT%
echo.

if exist "%ROOT%\bin\miloco-mcp-server.exe" (
    echo [OK] Binary: bin\miloco-mcp-server.exe
) else (
    echo [FAIL] Binary not found: bin\miloco-mcp-server.exe
    echo        Run: scripts\setup.bat
    set /a ERRORS+=1
)

set N=0
for %%f in ("%ROOT%\lib\*.dll") do set /a N+=1
if !N! gtr 0 (echo [OK] Libraries: !N! DLLs in lib\) else (echo [WARN] lib\ is empty)

if exist "%ROOT%\config\config.yaml" (
    echo [OK] Config: config\config.yaml
) else if exist "%ROOT%\config\config.yaml.example" (
    copy "%ROOT%\config\config.yaml.example" "%ROOT%\config\config.yaml" >nul
    echo [OK] Created config\config.yaml from example
) else (
    echo [FAIL] No config found
    set /a ERRORS+=1
)

if not exist "%ROOT%\data" mkdir "%ROOT%\data"
echo [OK] Data directory: data\

if exist "%ROOT%\webui" echo [OK] WebUI: webui\

echo.
if !ERRORS! gtr 0 (
    echo FAILED: !ERRORS! errors. Run: scripts\setup.bat
    exit /b 1
) else (
    echo All checks passed.
    echo Next: edit config\config.yaml, then: scripts\start.bat
)

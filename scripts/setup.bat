@echo off
setlocal enabledelayedexpansion
:: FeyaGate Skill — Windows Setup
::
:: Finds matching release .zip in packages\, extracts to bin\, lib\, webui\.
::
:: Usage:
::   scripts\setup.bat                                    Auto-detect
::   scripts\setup.bat --package packages\xxx.zip         Specify archive

set "ROOT=%~dp0.."
set "PKG_DIR=%ROOT%\packages"
set "BIN_DIR=%ROOT%\bin"
set "LIB_DIR=%ROOT%\lib"
set "DATA_DIR=%ROOT%\data"
set "CONFIG_DIR=%ROOT%\config"
set "ARCHIVE="

:: Parse arguments
:parse_args
if "%~1"=="" goto :main
if "%~1"=="--package" (set "ARCHIVE=%~2" & shift & shift & goto :parse_args)
if "%~1"=="--help" goto :help
if "%~1"=="-h" goto :help
echo Unknown option: %~1
goto :help

:help
echo FeyaGate Skill — Windows Setup
echo.
echo Usage:
echo   scripts\setup.bat                              Auto-detect package
echo   scripts\setup.bat --package ^<archive.zip^>    Specify archive
echo.
echo Place the release .zip in the packages\ directory:
echo   packages\miloco-mcp-server-VERSION-Windows-x86_64.zip
echo.
echo Download from: https://gitee.com/panjyang/miloco-mcp-server/releases
exit /b 0

:main
echo === FeyaGate Skill — Setup (Windows) ===
echo Root: %ROOT%
echo.

:: Find package if not specified
if defined ARCHIVE goto :extract
for %%f in ("%PKG_DIR%\miloco-mcp-server-*Windows*.zip") do (
    if exist "%%f" (set "ARCHIVE=%%f" & goto :extract)
)
for %%f in ("%ROOT%\miloco-mcp-server-*Windows*.zip") do (
    if exist "%%f" (set "ARCHIVE=%%f" & goto :extract)
)

echo ERROR: No matching Windows release package found.
echo.
echo Please download and place in packages\ directory:
echo   packages\miloco-mcp-server-VERSION-Windows-x86_64.zip
echo.
echo Download from: https://gitee.com/panjyang/miloco-mcp-server/releases
exit /b 1

:extract
echo Extracting: %ARCHIVE%

:: Extract to temp directory
set "TMP_DIR=%TEMP%\feyagate-setup-%RANDOM%"
mkdir "%TMP_DIR%" 2>nul
powershell -command "Expand-Archive -Path '%ARCHIVE%' -DestinationPath '%TMP_DIR%' -Force"

:: Find inner directory
set "INNER="
for /d %%d in ("%TMP_DIR%\*") do (set "INNER=%%d" & goto :deploy)
set "INNER=%TMP_DIR%"

:deploy
:: Deploy binary
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"
if exist "%INNER%\miloco-mcp-server.exe" (
    copy /y "%INNER%\miloco-mcp-server.exe" "%BIN_DIR%\" >nul
    echo   [OK] bin\miloco-mcp-server.exe
) else if exist "%INNER%\bin\miloco-mcp-server.exe" (
    copy /y "%INNER%\bin\miloco-mcp-server.exe" "%BIN_DIR%\" >nul
    echo   [OK] bin\miloco-mcp-server.exe
) else (
    echo   [WARN] Binary not found in archive
)

:: Deploy libraries
if not exist "%LIB_DIR%" mkdir "%LIB_DIR%"
set LIB_COUNT=0
if exist "%INNER%\lib" (
    for %%f in ("%INNER%\lib\*.*") do (
        copy /y "%%f" "%LIB_DIR%\" >nul
        set /a LIB_COUNT+=1
    )
)
echo   [OK] lib\ (!LIB_COUNT! libraries)

:: Deploy WebUI
if exist "%INNER%\webui" (
    if exist "%ROOT%\webui" rmdir /s /q "%ROOT%\webui"
    xcopy /e /i /q "%INNER%\webui" "%ROOT%\webui" >nul
    echo   [OK] webui\
)

:: Deploy default config
if not exist "%CONFIG_DIR%\config.yaml" (
    if exist "%INNER%\config.yaml" (
        copy /y "%INNER%\config.yaml" "%CONFIG_DIR%\config.yaml" >nul
        echo   [OK] config\config.yaml
    ) else if exist "%CONFIG_DIR%\config.yaml.example" (
        copy /y "%CONFIG_DIR%\config.yaml.example" "%CONFIG_DIR%\config.yaml" >nul
        echo   [OK] config\config.yaml (from example)
    )
)

:: Cleanup temp
rmdir /s /q "%TMP_DIR%" 2>nul

:: Create data directory
if not exist "%DATA_DIR%" mkdir "%DATA_DIR%"

:: Verify
echo.
echo --- Verification ---
if exist "%BIN_DIR%\miloco-mcp-server.exe" (echo [OK] Binary: bin\miloco-mcp-server.exe) else (echo [FAIL] Binary not found)

set N=0
for %%f in ("%LIB_DIR%\*.dll") do set /a N+=1
echo [OK] Libraries: !N! DLLs in lib\

if exist "%CONFIG_DIR%\config.yaml" (echo [OK] Config: config\config.yaml) else (echo [WARN] Config not found)
echo [OK] Data directory: data\

echo.
echo Setup complete! Next steps:
echo   1. Edit config\config.yaml (set cloud_server region)
echo   2. scripts\start.bat
echo   3. python3 scripts\auth.py  (first-time authorization)
echo   4. scripts\health_check.bat

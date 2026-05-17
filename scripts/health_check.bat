@echo off
set "ROOT=%~dp0.."
set "PORT=38080"
:: Read port from config.yaml
if exist "%ROOT%\config\config.yaml" (
    for /f "tokens=2 delims=: " %%a in ('findstr /r "http_port:" "%ROOT%\config\config.yaml"') do set "PORT=%%a"
)
if "%~1"=="--port" set "PORT=%~2"
echo === Health Check (http://localhost:%PORT%) ===
curl -s -o nul -w "%%{http_code}" "http://localhost:%PORT%/health" > "%TEMP%\_mhc.tmp" 2>nul
set /p HC=<"%TEMP%\_mhc.tmp" & del "%TEMP%\_mhc.tmp" 2>nul
if "%HC%"=="200" (echo [OK] HTTP 200) else (echo [FAIL] HTTP %HC% & exit /b 1)
curl -s -X POST "http://localhost:%PORT%/mcp/http" -H "Content-Type: application/json" -d "{\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"tools/call\",\"params\":{\"name\":\"xiaomi/auth_status\",\"arguments\":{}}}" 2>nul | python3 -c "import sys,json;r=json.load(sys.stdin);d=json.loads(r['result']['content'][0]['text']);print(f'Auth: {\"Yes\" if d.get(\"authorized\") else \"No\"} ({d.get(\"cloud_server\",\"?\")})')" 2>nul

@echo off
echo Stopping miloco-mcp-server...
tasklist /FI "IMAGENAME eq miloco-mcp-server.exe" /FO CSV /NH 2>nul | findstr /i "miloco-mcp-server" >nul 2>&1
if errorlevel 1 (echo Not running. & exit /b 0)
taskkill /IM miloco-mcp-server.exe >nul 2>&1
timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq miloco-mcp-server.exe" /FO CSV /NH 2>nul | findstr /i "miloco-mcp-server" >nul 2>&1
if not errorlevel 1 (taskkill /F /IM miloco-mcp-server.exe >nul 2>&1)
echo Stopped.

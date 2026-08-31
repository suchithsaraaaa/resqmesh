@echo off
:: ResQMesh AI - Windows Firewall Configuration Utility
:: Run as Administrator to allow P2P mesh discovery (UDP 52525) and HTTP API (TCP 8000)

echo ===================================================
echo   ResQMesh AI - Offline Mesh Firewall Setup
echo ===================================================
echo.

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] This script requires Administrator privileges.
    echo Please right-click configure_firewall.bat and select "Run as administrator".
    pause
    exit /b 1
)

echo [1/3] Adding inbound rule for ResQMesh HTTP API (TCP 8000)...
netsh advfirewall firewall add rule name="ResQMesh AI Backend API" dir=in action=allow protocol=TCP localport=8000 profile=any >nul 2>&1

echo [2/3] Adding inbound rule for ResQMesh P2P UDP Discovery (UDP 52525)...
netsh advfirewall firewall add rule name="ResQMesh AI Mesh Discovery" dir=in action=allow protocol=UDP localport=52525 profile=any >nul 2>&1

echo [3/3] Adding inbound rule for mDNS Zeroconf Discovery (UDP 5353)...
netsh advfirewall firewall add rule name="ResQMesh AI mDNS Discovery" dir=in action=allow protocol=UDP localport=5353 profile=any >nul 2>&1

echo.
echo [SUCCESS] Windows Firewall rules configured successfully!
echo Laptops on the same Wi-Fi / Hotspot / LAN can now discover and sync peer-to-peer.
echo.
pause

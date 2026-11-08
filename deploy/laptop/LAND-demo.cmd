@echo off
rem LAND judge demo: opens the demo page served by the box in its own window.
rem The laptop must be on the same Wi-Fi as the box. Optional: LAND-demo.cmd <box address>
set "HOST=%~1"
if not "%HOST%"=="" goto open
for %%h in (rafhost.local 172.20.10.6) do (
  ping -n 1 -w 1500 %%h >nul && ( set "HOST=%%h" & goto open )
)
echo Box not found. Join the same Wi-Fi as the box, or run: LAND-demo.cmd ^<box IP^>
pause
exit /b 1
:open
echo Opening http://%HOST%:8080/demo/
start "" msedge --app=http://%HOST%:8080/demo/ --start-maximized

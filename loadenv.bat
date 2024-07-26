@echo off
setlocal enabledelayedexpansion
for /f "tokens=1,* delims==" %%a in (.env) do (
    set %%a=%%b
)
endlocal & (
    set "APP_PATH=%APP_PATH%"
)

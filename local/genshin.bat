@echo off

call loadenv.bat
call ../venv/Scripts/activate

@REM Random color for cmd
Set /a num=(%Random% %%9)+1
color %num%

@REM Check 'today login status'
@REM 1: Already login
@REM 2: Not login
@REM 3: File not found
for /f %%a in ('python daycheck.py') do set result=%%a

if "%result%"=="1" (
    start "" %APP_PATH%
    exit
) else if "%result%"=="2" (
    echo Hom nay chua diem danh...
    python dailyCheckin.py
    start "" %APP_PATH%
    pause
    exit
) else if "%result%"=="3" (
    echo Khong tim thay file daycheck.txt, dang tao file moi...
    python autoDaily.py
    start "" %APP_PATH%
    pause
    exit
) else (
    echo Error: %result%
    start "" %APP_PATH%
    pause
    exit
)
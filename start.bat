@echo off
setlocal
pushd "%~dp0" >nul 2>&1
if errorlevel 1 goto bad_folder
title VoiceLoom
call "%~dp0find_python.bat"
if not defined NARRATOR_PY goto no_python
echo Starting with: "%NARRATOR_PY%"
"%NARRATOR_PY%" "%~dp0launcher.py" %*
set "NARRATOR_EXIT=%errorlevel%"
if "%NARRATOR_EXIT%"=="0" exit /b 0
echo.
echo App stopped with exit code %NARRATOR_EXIT%.
echo Read logs\startup.log, or run diagnose.bat for more details.
echo On a new laptop run setup.bat first. Copy the WHOLE folder.
pause
exit /b %NARRATOR_EXIT%
:no_python
echo Python 3.10-3.12 64-bit was not found or cannot run.
echo Install Python 3.12 64-bit from https://www.python.org/downloads/windows/
echo Include pip and Tcl/Tk, then run setup.bat and start.bat.
echo A virtual environment copied from another PC will not work reliably.
pause
exit /b 1
:bad_folder
echo Extract the whole project ZIP into Documents\VoiceLoom and try again.
pause
exit /b 1

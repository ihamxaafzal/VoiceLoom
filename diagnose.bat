@echo off
setlocal
pushd "%~dp0" >nul 2>&1
if errorlevel 1 goto folder_error
title VoiceLoom - Diagnostics
call "%~dp0find_python.bat"
if not defined NARRATOR_PY goto no_python
"%NARRATOR_PY%" "%~dp0launcher.py" --diagnose
echo.
echo Share logs\diagnostic.log to identify this computer's startup problem.
pause
exit /b 0
:no_python
echo No working Python 3.10-3.12 64-bit was found on this laptop.
echo Install Python 3.12 64-bit with pip and Tcl/Tk, then run setup.bat.
pause
exit /b 1
:folder_error
echo Extract the whole project ZIP into Documents\VoiceLoom and try again.
pause
exit /b 1

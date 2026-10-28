@echo off
setlocal
set "NARRATOR_PY="
title VoiceLoom - Laptop Setup
pushd "%~dp0" >nul 2>&1
if errorlevel 1 goto folder_error
if not exist "%CD%\find_python.bat" goto incomplete
if not exist "%CD%\setup_project.py" goto incomplete
call "%CD%\find_python.bat" --base
if not defined NARRATOR_PY goto no_python
echo VoiceLoom - laptop setup
echo Installing with "%NARRATOR_PY%"
echo Keep internet connected. Local speech packages need several GB of free disk space.
"%NARRATOR_PY%" "%CD%\setup_project.py" %*
set "NARRATOR_RESULT=%errorlevel%"
echo.
if not "%NARRATOR_RESULT%"=="0" echo Python/setup stopped with exit code %NARRATOR_RESULT%.
if "%NARRATOR_RESULT%"=="-1073741819" echo Python itself crashed with Access Violation 0xC0000005. Repair Python first.
if not "%NARRATOR_RESULT%"=="0" echo Share logs\setup.log if it was created.
pause
popd
exit /b %NARRATOR_RESULT%
:incomplete
echo Project files are missing beside setup.bat.
echo Extract the WHOLE ZIP first. Do not run setup from inside the ZIP preview.
goto failed
:no_python
echo No working Python 3.10-3.12 64-bit was found.
echo Install Python 3.12 64-bit with pip and Tcl/Tk from python.org.
goto failed
:folder_error
echo Windows could not open the project folder.
echo Extract the ZIP into Documents\VoiceLoom and try again.
:failed
pause
exit /b 1

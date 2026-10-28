@echo off
rem Returns a tested 64-bit Python 3.10-3.12 in NARRATOR_PY.
set "NARRATOR_PY="
if /i "%~1"=="--base" goto base_python
call :probe "%~dp0.venv\Scripts\python.exe"
if defined NARRATOR_PY exit /b 0
:base_python
for %%V in (312 311 310) do (
    call :probe "%LocalAppData%\Programs\Python\Python%%V\python.exe"
    if defined NARRATOR_PY exit /b 0
)
for %%V in (3.12 3.11 3.10) do (
    for /f "delims=" %%P in ('py -%%V -c "import sys; print(sys.executable)" 2^>nul') do call :probe "%%P"
    if defined NARRATOR_PY exit /b 0
)
for /f "delims=" %%P in ('where python.exe 2^>nul') do (
    call :probe "%%P"
    if defined NARRATOR_PY exit /b 0
)
exit /b 1
:probe
if defined NARRATOR_PY exit /b 0
if not exist "%~1" exit /b 1
"%~1" -c "import sys; raise SystemExit(not ((3,10) <= sys.version_info < (3,13) and sys.maxsize > 2**32))" >nul 2>&1
rem Native crashes can have NEGATIVE exit codes; IF ERRORLEVEL 1 misses them.
if not "%errorlevel%"=="0" exit /b 1
set "NARRATOR_PY=%~1"
exit /b 0

@echo off
echo ============================================
echo Deleting Test Files from Local Disk
echo ============================================
echo.

echo Deleting test Python files...
del /F /Q test_*.py 2>nul
if %errorlevel% equ 0 (
    echo [OK] Python test files deleted
) else (
    echo [INFO] No Python test files found or already deleted
)

echo.
echo Deleting test HTML files...
del /F /Q test_*.html 2>nul
if %errorlevel% equ 0 (
    echo [OK] HTML test files deleted
) else (
    echo [INFO] No HTML test files found or already deleted
)

echo.
echo Deleting sample HTML files...
del /F /Q sample_*.html 2>nul
if %errorlevel% equ 0 (
    echo [OK] Sample HTML files deleted
) else (
    echo [INFO] No sample HTML files found or already deleted
)

echo.
echo ============================================
echo Cleanup Complete!
echo ============================================
echo.
echo Test files have been deleted from your local disk.
echo.
pause

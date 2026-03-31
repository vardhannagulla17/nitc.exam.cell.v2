@echo off
echo Removing test files from git repository...
echo.

git rm --cached test_*.py 2>nul
git rm --cached test_*.html 2>nul

echo.
echo Test files have been unstaged from git.
echo They will be ignored in future commits due to .gitignore
echo.
echo To complete the removal, run:
echo   git commit -m "Remove test files from repository"
echo   git push
echo.
pause

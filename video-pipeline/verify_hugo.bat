@echo off
set LOG=%~dp0_hugo_verify.txt
cd /d "%~dp0.."
echo hugo build check > "%LOG%"
hugo --buildFuture >> "%LOG%" 2>&1
echo EXIT %errorlevel% >> "%LOG%"

@echo off
cd /d "%~dp0.."
python video-pipeline\nightly_head.py --dry > video-pipeline\_queue_test.txt 2>&1

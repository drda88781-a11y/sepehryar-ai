@echo off
chcp 65001 >nul
title تونل هوشمند دسترسی اینترنتی سپهریار
echo در حال بررسی و راه‌اندازی سرور و تونل اینترنتی...
py "%~dp0tunnel_runner.py"
pause


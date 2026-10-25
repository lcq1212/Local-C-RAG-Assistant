@echo off
chcp 65001 >nul
title RAG 系统一键启动台

echo =========================================
echo    正在唤醒分布式 RAG 智能问答系统...
echo =========================================

echo [1/3] 启动 本地 C 语言 Flask 后端...
start "本地后端 (Flask)" cmd /k "python local_server.py"

echo [2/3] 启动 网页前端 (Streamlit)...
start "网页前端 (Streamlit)" cmd /k "streamlit run web_app.py"

echo [3/3] 启动 公网隧道 (前端 & 后端)...
start "后端穿透 (5000)" cmd /k "cpolar http 5000"
start "前端穿透 (8501)" cmd /k "cpolar http 8501"

echo.
echo =========================================
echo 启动完毕！
echo 1. 去 5000 窗口找地址填入 web_app.py（如果没变就不用填）。
echo 2. 去 8501 窗口找 https 网址，发给朋友！
echo 3. 网页输入密码 admin888 开始使用。
echo =========================================
echo.
pause
@echo off
chcp 65001 >nul
title 纯本地 RAG 一键启动

echo =========================================
echo    正在启动全本地 RAG 智能知识库...
echo =========================================

echo [1/2] 检查 Ollama 服务...
start "Ollama 服务" cmd /k "ollama run qwen2.5:3b"

echo [2/2] 启动 Streamlit 网页...
start "网页前端" cmd /k "streamlit run web_app.py"

echo.
echo 启动完毕！浏览器将自动打开。
pause
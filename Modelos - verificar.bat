@echo off
rem Modelos ArqSynth, Fase 1: ver a pasta partilhada dos modelos, criar um exemplo, ler, definir o padrao,
rem sem abrir o ArqSynth BIM. Corre no Linux do Windows (WSL), como o programa.
chcp 65001 >nul
cd /d "%~dp0"
set WSL_UTF8=1
wsl.exe -d Ubuntu-24.04 -u root --cd "%~dp0." -- env QT_QPA_PLATFORM=offscreen /opt/arqbim/venv/bin/python scripts/modelos.py
pause

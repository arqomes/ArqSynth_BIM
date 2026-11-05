@echo off
rem Abre o ArqBIM diretamente no Windows (o Python de .venv). Desde 2026-10-22 o Smart App Control do
rem Windows bloqueia bibliotecas do IfcOpenShell e este arranque falha: use ArqBIM.bat (Linux do Windows, WSL).
rem Erros ficam em %LOCALAPPDATA%\ArqSynth BIM\arqbim.log (ate a 0.76: ArqBIM)
cd /d "%~dp0"
start "" ".venv\Scripts\pythonw.exe" -m arqbim

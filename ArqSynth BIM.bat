@echo off
rem Abre o ArqSynth BIM (duplo clique; ate a 0.76 chamava-se ArqBIM). Corre no Linux do Windows (WSL,
rem Ubuntu-24.04) desde 2026-10-22: o Smart App Control do Windows bloqueia bibliotecas nao assinadas do
rem IfcOpenShell. A janela aparece como as outras.
rem Preparar o Linux (uma vez):  wsl -d Ubuntu-24.04 -u root -- bash /mnt/c/BIM/scripts/wsl_setup.sh
rem Erros: \\wsl.localhost\Ubuntu-24.04\root\ArqSynth BIM\arqbim.log (ate a 0.76: \root\ArqBIM)      Sem o Linux: ArqBIM-Windows.bat
cd /d "%~dp0"
set WSL_UTF8=1
wsl.exe -l -q 2>nul | findstr /c:"Ubuntu-24.04" >nul
if errorlevel 1 (
    echo O Linux do Windows ^(WSL, Ubuntu-24.04^) nao esta instalado: o ArqSynth BIM precisa dele.
    echo Veja ARQUITETURA.md, "Como abrir".
    pause
    exit /b 1
)
powershell -NoProfile -WindowStyle Hidden -Command "Start-Process wsl.exe -WindowStyle Hidden -ArgumentList '-d','Ubuntu-24.04','-u','root','--cd','%~dp0.','--','bash','scripts/arqbim_wsl.sh'"
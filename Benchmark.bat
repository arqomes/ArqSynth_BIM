@echo off
rem Mede a velocidade do ArqBIM (instrucoes, seccao 6) e acrescenta os resultados a benchmark\resultados.md
rem   Benchmark.bat                       edificio gerado pelo programa (tamanho "medio")
rem   Benchmark.bat --tamanho grande      pequeno / medio / grande
rem   Benchmark.bat C:\obra\projeto.ifc   qualquer IFC (por exemplo exportado do Revit)
cd /d "%~dp0"
".venv\Scripts\python.exe" -W ignore scripts\benchmark.py %*
echo.
echo Resultados completos em benchmark\resultados.md
pause

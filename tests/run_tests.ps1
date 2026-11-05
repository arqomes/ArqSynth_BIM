# Runs all tests — in Linux (WSL, Ubuntu-24.04), where ArqBIM runs since 2026-10-22 (Windows' Smart App
# Control blocks IfcOpenShell's unsigned libraries). See tests/run_tests.sh.
#   powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1          core tests (no window)
#   powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1 -Gui     + opens the app and drives it
#   powershell -ExecutionPolicy Bypass -File tests\run_tests.ps1 -Windows  in Windows' own .venv (if allowed)
param([switch]$Gui, [switch]$Windows)
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
$code = 0
if ($Windows) {
    $py = Join-Path $root ".venv\Scripts\python.exe"
    & $py -m unittest discover -s tests
    if ($LASTEXITCODE -ne 0) { $code = 1 }
    if ($Gui) {
        & $py tests\gui_smoke.py
        if ($LASTEXITCODE -ne 0) { $code = 1 }
    }
} else {
    $env:WSL_UTF8 = "1"
    $wslArgs = @("-d", "Ubuntu-24.04", "-u", "root", "--cd", $root, "--", "bash", "tests/run_tests.sh")
    if ($Gui) { $wslArgs += "--gui" }
    & wsl.exe @wslArgs
    if ($LASTEXITCODE -ne 0) { $code = 1 }
}
Pop-Location
exit $code

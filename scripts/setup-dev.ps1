param([switch]$SkipDownloads)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
function Invoke-CheckedPython {
    & $pythonExe @args
    if ($LASTEXITCODE -ne 0) { throw "Python 步骤失败：$args" }
}
if (-not (Test-Path -LiteralPath $pythonExe)) {
    if (-not (Get-Command py -ErrorAction SilentlyContinue)) { throw '请先安装 Python 3.12 x64（含 py 启动器）。' }
    & py -3.12 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw '创建 Python 3.12 环境失败' }
}
Invoke-CheckedPython -c "import sys,struct; assert sys.version_info[:2]==(3,12) and struct.calcsize('P')==8, '需要 Python 3.12 x64；请检查 .venv'"
Invoke-CheckedPython -m pip install --only-binary=:all: -r requirements.lock.txt
Invoke-CheckedPython -m pip install --no-deps --no-build-isolation -e .
Invoke-CheckedPython scripts/build_demo_dictionaries.py
if (-not $SkipDownloads) {
    & $pythonExe -c "import sqlite3; c=sqlite3.connect('file:resources/dictionaries/english.db?mode=ro',uri=True); n=c.execute('select count(*) from entries').fetchone()[0]; c.close(); raise SystemExit(0 if n>=500000 else 1)"
    if ($LASTEXITCODE -ne 0) { Invoke-CheckedPython scripts/install_ecdict.py }
    $modelsComplete = $true
    $translationPairs = @('en_zh')
    & $pythonExe -c "from pathlib import Path; from grepzztranslate.japanese_model import JapaneseModelService; raise SystemExit(0 if JapaneseModelService(Path('resources/translation/ja_en_lfm')).available() else 1)"
    if ($LASTEXITCODE -ne 0) { $translationPairs += 'ja_en' }
    foreach ($pair in $translationPairs) {
        foreach ($file in @('model\model.bin', 'sentencepiece.model', 'metadata.json')) {
            if (-not (Test-Path -LiteralPath "resources\translation\$pair\$file")) { $modelsComplete = $false }
        }
    }
    if (-not $modelsComplete) { Invoke-CheckedPython scripts/install_translation_models.py }
}
Invoke-CheckedPython scripts/check-dev.py
Write-Output '开发环境就绪。启动源码：.\.venv\Scripts\python.exe run.py'

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
$pythonExe = Join-Path $projectRoot '.venv\Scripts\python.exe'
& $pythonExe scripts/build_demo_dictionaries.py
if ($LASTEXITCODE -ne 0) { throw '测试字典生成失败' }
& $pythonExe -c "import sqlite3; c=sqlite3.connect('file:resources/dictionaries/english.db?mode=ro',uri=True); n=c.execute('SELECT count(*) FROM entries').fetchone()[0]; c.close(); raise SystemExit(0 if n >= 500000 else 1)"
if ($LASTEXITCODE -ne 0) { throw '发行包需要完整英语词库。请先运行 .venv\Scripts\python.exe scripts/install_ecdict.py' }
# 個人データがある配布先を PyInstaller で削除しない。
& $pythonExe -m PyInstaller --noconfirm --distpath build/package GrepzzTranslate.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller 构建失败' }
$bundle = Join-Path $projectRoot 'build\package\GrepzzTranslate'
New-Item -ItemType Directory -Force -Path "$bundle\resources\dictionaries", "$bundle\resources\sudachi", "$bundle\data" | Out-Null
Copy-Item -LiteralPath 'resources\dictionaries\english.db', 'resources\dictionaries\japanese.db' -Destination "$bundle\resources\dictionaries"
$sudachiDictionary = & $pythonExe -c "import sudachidict_core; print(sudachidict_core.__path__[0])"
if ($LASTEXITCODE -ne 0) { throw '找不到 Sudachi 字典' }
Copy-Item -LiteralPath (Join-Path $sudachiDictionary 'resources\system.dic') -Destination "$bundle\resources\sudachi\system.dic"
foreach ($pair in @('en_zh', 'ja_en')) {
    if (-not (Test-Path "resources\translation\$pair\model\model.bin")) { throw '请先运行 scripts/install_translation_models.py 下载离线翻译模型' }
}
Copy-Item -LiteralPath 'resources\translation' -Destination "$bundle\resources" -Recurse -Force
if (-not (Test-Path -LiteralPath "$bundle\config.json")) {
    Copy-Item -LiteralPath 'config.example.json' -Destination "$bundle\config.json"
}
if (Test-Path -LiteralPath 'resources\licenses') {
    Copy-Item -LiteralPath 'resources\licenses' -Destination "$bundle\resources" -Recurse -Force
}
Copy-Item -LiteralPath 'README.md', 'THIRD_PARTY_NOTICES.md' -Destination $bundle
$releaseBundle = Join-Path $projectRoot 'dist\GrepzzTranslate'
New-Item -ItemType Directory -Force -Path $releaseBundle | Out-Null
# 設定と履歴は利用者のものを維持する。
Get-ChildItem -LiteralPath $bundle | Where-Object { $_.Name -notin @('data', 'logs', 'config.json') } | Copy-Item -Destination $releaseBundle -Recurse -Force
if (-not (Test-Path -LiteralPath "$releaseBundle\config.json")) {
    Copy-Item -LiteralPath 'config.example.json' -Destination "$releaseBundle\config.json"
}
& $pythonExe scripts/collect_licenses.py
if ($LASTEXITCODE -ne 0) { throw '许可文件收集失败' }
Write-Output "构建完成: $releaseBundle\GrepzzTranslate.exe"

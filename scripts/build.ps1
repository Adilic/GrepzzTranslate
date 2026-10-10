param([string]$JapaneseModelPath = '')
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
if (-not $JapaneseModelPath -and (Test-Path -LiteralPath 'resources\translation\ja_en_lfm\metadata.json')) {
    $JapaneseModelPath = Join-Path $projectRoot 'resources\translation\ja_en_lfm'
}
$pairs = @('en_zh')
if ($JapaneseModelPath) {
    $JapaneseModelPath = (Resolve-Path -LiteralPath $JapaneseModelPath).Path
    & $pythonExe -c "import sys; from pathlib import Path; from grepzztranslate.japanese_model import JapaneseModelService; raise SystemExit(0 if JapaneseModelService(Path(sys.argv[1])).available() else 1)" $JapaneseModelPath
    if ($LASTEXITCODE -ne 0) { throw '可选日语模型资源不完整，请重新运行 scripts/install_japanese_model.py' }
} else {
    $pairs += 'ja_en'
}
foreach ($pair in $pairs) {
    if (-not (Test-Path "resources\translation\$pair\model\model.bin")) { throw '请先运行 scripts/install_translation_models.py 下载离线翻译模型' }
}
$translationBundle = Join-Path $bundle 'resources\translation'
New-Item -ItemType Directory -Force -Path $translationBundle | Out-Null
foreach ($pair in $pairs) {
    Copy-Item -LiteralPath "resources\translation\$pair" -Destination $translationBundle -Recurse -Force
}
if ($JapaneseModelPath) {
    $modelBundle = Join-Path $translationBundle 'ja_en_lfm'
    New-Item -ItemType Directory -Force -Path $modelBundle | Out-Null
    Get-ChildItem -LiteralPath $JapaneseModelPath | Copy-Item -Destination $modelBundle -Recurse -Force
    $pairs += 'ja_en_lfm'
}
if (-not (Test-Path -LiteralPath "$bundle\config.json")) {
    Copy-Item -LiteralPath 'config.example.json' -Destination "$bundle\config.json"
}
if (Test-Path -LiteralPath 'resources\licenses') {
    Copy-Item -LiteralPath 'resources\licenses' -Destination "$bundle\resources" -Recurse -Force
}
Copy-Item -LiteralPath 'README.md', 'THIRD_PARTY_NOTICES.md' -Destination $bundle
$releaseBundle = Join-Path $projectRoot 'dist\GrepzzTranslate'
New-Item -ItemType Directory -Force -Path $releaseBundle | Out-Null
# Archive previously packaged model candidates so they do not inflate the release.
foreach ($oldPair in @('ja_en', 'ja_zh', 'ja_en_lfm')) {
    $oldPath = Join-Path $releaseBundle "resources\translation\$oldPair"
    if ($oldPair -notin $pairs -and (Test-Path -LiteralPath $oldPath)) {
        $backupPath = Join-Path $projectRoot ('build\model-backups\' + [guid]::NewGuid().ToString('N') + '\' + $oldPair)
        $sourceFull = [IO.Path]::GetFullPath($oldPath)
        $backupFull = [IO.Path]::GetFullPath($backupPath)
        $rootPrefix = [IO.Path]::GetFullPath($projectRoot).TrimEnd('\') + '\'
        if (-not $sourceFull.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase) -or -not $backupFull.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) { throw '模型归档路径超出项目目录' }
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $backupFull) | Out-Null
        Move-Item -LiteralPath $sourceFull -Destination $backupFull
    }
}
# 設定と履歴は利用者のものを維持する。
Get-ChildItem -LiteralPath $bundle | Where-Object { $_.Name -notin @('data', 'logs', 'config.json') } | Copy-Item -Destination $releaseBundle -Recurse -Force
if (-not (Test-Path -LiteralPath "$releaseBundle\config.json")) {
    Copy-Item -LiteralPath 'config.example.json' -Destination "$releaseBundle\config.json"
}
& $pythonExe scripts/collect_licenses.py --destination "$releaseBundle\licenses"
if ($LASTEXITCODE -ne 0) { throw '许可文件收集失败' }
Write-Output "构建完成: $releaseBundle\GrepzzTranslate.exe"

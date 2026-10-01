from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_dynamic_libs

root = Path(SPECPATH)
sudachi_data, sudachi_binaries, sudachi_hidden = collect_all('sudachipy')
hidden = sudachi_hidden + collect_submodules('winrt')
a = Analysis([str(root / 'run.py')], pathex=[str(root / 'src')],
             binaries=sudachi_binaries + collect_dynamic_libs('ctranslate2'), datas=sudachi_data, hiddenimports=hidden,
             excludes=['tkinter', 'pytest'], noarchive=False)
# Qt は Windows の ICU を使用し、ビルド用 Python の同名 DLL は含めない。
a.binaries = [item for item in a.binaries if Path(item[0]).name.lower() not in {'icuuc.dll', 'icudt78.dll'}]
# Sudachi 辞書は resources/sudachi に一度だけ配置する。
a.datas = [item for item in a.datas if not item[0].replace('\\', '/').startswith('sudachidict_core/resources/')]
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='GrepzzTranslate',
          debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
          console=os.environ.get('GREPZZ_CONSOLE') == '1')
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='GrepzzTranslate')

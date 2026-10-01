# 第三方组件

GrepzzTranslate 在运行时不调用云服务。以下依赖及数据遵循各自的许可；本文件不改变上游许可。

- Python：PSF License。https://www.python.org/psf/license/
- PySide6 / Qt for Python：LGPLv3 / GPLv3 或商业许可，具体组件见随包许可及 https://doc.qt.io/qtforpython-6/licenses.html 。本项目使用动态链接 Qt Core / Gui / Widgets，允许替换相应动态库。源代码及对应版本可从 https://download.qt.io/official_releases/QtForPython/ 获取。
- SudachiPy：Apache License 2.0。https://github.com/WorksApplications/SudachiPy
- SudachiDict：Apache License 2.0 及上游词典声明。https://github.com/WorksApplications/SudachiDict
- PyWinRT：MIT License。https://github.com/pywinrt/pywinrt
- PyInstaller：GPL 2.0，含生成应用的分发例外。https://pyinstaller.org/en/stable/license.html
- Windows OCR 引擎与语言资源：系统组件，由 Microsoft 授权提供，不包含在本项目分发目录中。

英语词库由 [ECDICT](https://github.com/skywind3000/ECDICT) 的 `ecdict.csv` 转换为 SQLite。保留词条释义、音标与词形，增加本项目表结构与数据来源记录。上游许可证原文随包保存在 `resources/licenses/ECDICT-LICENSE.txt`。来源 CSV SHA256：`1a6947e04785db63613a92e14903cdae7954f7e84860b10e68e5c7cbb3f9c3cf`。演示日语词条为本项目手工编写的少量测试数据；JMdict 尚未引入。

打包脚本将已安装 Python 依赖的许可文件收集到 `licenses/`。公开分发前应保留本说明、上游许可和修改说明，检查所用确切版本的许可要求。
# 离线翻译模型（v0.1.4）

使用 Argos 官方索引 https://github.com/argosopentech/argospm-index 中的 English→Chinese 1.9、Japanese→English 1.1 模型。原始包下载地址与 SHA256 保存在 resources/translation/*/provenance.json，原作者说明保存在同目录 README.md；仅提取推理模型与分词器，未改动权重。英中包声明其 OPUS-MT 原始模型为 CC-BY 4.0，作者 Jörg Tiedemann、Santhosh Thottingal；日英包的数据作者及论文详见所附 README。运行时使用 CTranslate2（MIT）与 SentencePiece（Apache-2.0），依赖许可证随包附带。日语中文通过英语中转。


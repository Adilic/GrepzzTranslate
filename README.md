# GrepzzTranslate

**学习适用于不同项目的 Python 工程基础：阅读 [三册通用教材](docs/python-course/README.md)。** 从进程、解释器和 import 原理讲到依赖、结构、测试、打包与迁移，附独立可运行项目、六个实验、故障案例和答案。原先以本项目为例的 [入门说明](docs/PYTHON_ENVIRONMENT_TEXTBOOK.md) 仍保留，可用来对照。

**两台电脑继续开发？先看 [双机开发与项目理解手册](docs/DEVELOPMENT.md)。** 首次克隆后执行 `powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1`；环境检查使用 `.\.venv\Scripts\python.exe scripts/check-dev.py`。手册涵盖部署、资源迁移、Git 接力、架构、测试和排错。

Windows 本地英语 / 日语阅读翻译工具。**选中文字后按 Alt + 1**，直接查词或翻译，无需截图、无需手动复制；无法选中文字时，仍可按 **Alt + Q** 截图翻译。看完点击窗口外即可继续阅读，Esc 也可关闭。

**v0.1.7 日语模型更新**：支持 LFM2-350M-ENJP-MT Q4_K_M（日英专用，权重 229,310,240 字节，约 229 MB / 219 MiB），接上现有英中模型输出中文，并保留 Sudachi 注音。短句在开发机通常约 0.6～0.8 秒，首次加载更慢；**复杂否定和长句仍可能译反，尚不能作为可靠的整页阅读译文**。模型采用 **LFM Open License v1.0**，属于开放权重许可，含商业营收限制，**不是 Apache/MIT**。当前主项目和主程序已使用此模型；未安装新模型的开发环境仍兼容原有模型。来源、对比和实际译文见 [日语模型实测](docs/JAPANESE_MODEL_EVALUATION.md)。

**阅读浮窗**：看完后直接点击窗口外任意位置即可收起，点击会继续传给原窗口；切换应用同样收起。识别过程中点击外部会取消这次结果的显示，识别结束不会再弹回来。Esc 仍可关闭。默认使用浅色、薄荷绿和圆角阴影，OCR 原文修正框默认隐藏，点击右上角“修正”再展开。

适用于 Kindle、PDF、网页、图片、扫描文档等屏幕内容。运行时不调用网络服务，不接入 AI / 翻译 API，不持续监听剪贴板。Alt+1 触发时，会临时模拟 Ctrl+C 读取当前选中文字，成功后恢复之前通过 Qt 读取到的剪贴板格式；若其他程序改写剪贴板则取消，避免覆盖新内容。某些软件专有的剪贴板格式不保证完整恢复。截图功能不使用剪贴板。截图只在内存中处理，不保存图片。查询文本保存到本机 `data/history.db`；日志默认不保存 OCR 原文，可在设置中开启。

**v0.1.1**：英语已接入 ECDICT 的 770,611 条词条，修复普通单词（例如 `Windows`）查不到的问题。浮窗顶部显示 OCR 原文，可用键盘修正后按 Enter 重查。单词和已收录短语优先查词典；v0.1.4 中未收录的英文短语、句子及日语文本使用离线模型生成中文。日语词典仍是小型演示词库。

**v0.1.4 离线短语与整句翻译**：英文直接译成中文，日语经英语中转为中文。译文优先显示，原文保留在下方。首次使用会加载本地模型，之后复用；不上传文字或截图。每次最多 1200 字符，过长选区请分段。机器译文可能出错，日语中转可能丢失细节。

**v0.1.5 日语注音**：日语结果优先显示带假名的原文，含汉字词语上方显示读音，下方保留中文译文。竖排截图识别后在浮窗中横排展示；注音由本地 Sudachi 生成，专名、多音字和 OCR 误字仍可能影响读音。

**v0.1.6 划词翻译**：在 Chrome 的可选择文本 PDF、网页或其他支持 Ctrl+C 的阅读器中选中文字，按 **Alt+1** 并松开。单词优先查本地词典，未命中则尝试本地模型；未收录短语和句子也由本地模型翻译，已收录短语保留词典释义。日语沿用汉字注音。选区读取失败会明确提示，不使用剪贴板里的旧文本。第一次模型翻译仍需加载模型。

## Alt + 1 划词翻译

1. 启动程序，等待资源就绪。
2. 在 Chrome PDF 或网页中选中 `book`，按 Alt+1 并松开，应显示词典释义。
3. 选中 `I am reading a book.` 再按 Alt+1，应显示本地模型译文；日语句子还会显示假名注音。
4. 点击阅读器中任意窗口外位置，结果收起；下一次选词后再按 Alt+1。
5. 没选中文字、PDF 禁止复制或只是扫描图片时，不会拿旧剪贴板内容翻译，改用 Alt+Q 截图。

Alt+1 固定用于划词，截图快捷键不能设成 Alt+1。读取时会等待 Alt 等按键松开；期间切换窗口会取消读取。阅读器和本工具应以相同权限运行，Windows 会限制向权限更高的程序模拟按键（[Microsoft SendInput 说明](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-sendinput)）。不需要浏览器扩展。剪贴板管理器、禁止复制的阅读器可能影响读取。

## 快速运行

已有打包程序时，双击项目根目录的「启动 GrepzzTranslate」快捷方式，或运行 `dist/GrepzzTranslate/GrepzzTranslate.exe`。请保留同目录下的 `_internal` 和 `resources` 文件夹，不要单独移动 exe。v0.1.3 修复缺资源启动后一直等待的问题，识别超时也会明确提示重试。

开发要求：Windows 10 / 11 x64、Python 3.12+。当前验证环境为 Python 3.12 x64。所有依赖使用预编译 wheel，不需要 Visual Studio。

在项目目录的 PowerShell 中执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe scripts/build_demo_dictionaries.py
.\.venv\Scripts\python.exe scripts/install_ecdict.py
.\.venv\Scripts\python.exe scripts/install_translation_models.py
.\.venv\Scripts\python.exe run.py
```

首次安装依赖及下载 ECDICT 需要联网；应用运行及查词完全本地。演示字典生成脚本不会覆盖已有字典，只有显式传入 `--force` 才会覆盖。`install_ecdict.py` 将英语词库替换为 ECDICT；也可用 `--csv 文件路径` 从本地 CSV 导入。

启动后显示系统托盘图标，关闭结果窗口不会退出程序。右键托盘可截图、打开设置、重新加载资源和退出。快捷键冲突会显示错误并写日志，仍可从托盘截图或更换快捷键。同一目录只运行一个实例。

## Alt + Q 测试

1. 启动程序，等待“已就绪”。
2. 打开任意网页 / PDF，或运行 `.\.venv\Scripts\python.exe scripts/reading_sample.py` 显示本地测试页。
3. 按 **Alt + Q**，屏幕变暗，拖动鼠标框选 `considerable`。
4. 松开后浮窗应显示音标及“相当大的”等中文释义；`Windows`、`apple` 等常见词也应能查到。
5. 直接点击阅读窗口，浮窗自动收起；再次框选 `経験`，应显示 `けいけん`。Esc 也可以关闭。
6. 框选 `deteriorated` 应查到恶化及词形说明；框选 `経験を積む` 应显示 `けいけんをつむ` 和 `积累经验`。
7. 框选中按 Esc 或右键应取消；空选区直接忽略，过小截图会提示重新框选。
8. OCR 识别错字时，点击浮窗右上角“修正”，用键盘修改原文后按 Enter 重查。未收录单词可能显示近似拼写候选。

首次 OCR 可能有系统组件初始化开销。识别期间界面保持响应，可按 Esc 隐藏等待浮窗，后续结果不会重新弹出；当前识别结束前不接受新的截图请求。

## OCR 方案与本地资源

使用 **Windows.Media.Ocr + PyWinRT**，直接调用 Windows 自带本地 OCR。英文和日文引擎在后台工作线程初始化并复用，无需 Paddle / PyTorch。图像先适度放大，限制到引擎允许的尺寸，再识别。日语引擎发现日文字符时优先采用日语结果，否则采用英文结果。

目标电脑需要安装 **英语和日语的 Windows OCR 可选语言资源**。语言资源属于 Windows，不随 exe 文件夹复制。缺少某种资源时程序明确提示，其余已安装语言仍可使用。

检查本机资源：

```powershell
.\.venv\Scripts\python.exe -c "from grepzztranslate.ocr import OCRService; print(OCRService.available_languages())"
```

在 Windows 设置 → 时间和语言 → 语言和区域 → 添加英语 / 日语 → 语言选项，安装相应基本输入和 OCR 资源。不同 Windows 版本选项名称可能不同。也可由用户在管理员 PowerShell 中按需执行（安装时需要系统下载）：

```powershell
Add-WindowsCapability -Online -Name 'Language.OCR~~~en-US~0.0.1.0'
Add-WindowsCapability -Online -Name 'Language.OCR~~~ja-JP~0.0.1.0'
```

安装后从托盘选择 **Reload Resources**。程序不会自动下载资源或更改系统设置。参考：[Microsoft OcrEngine](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine)、[OCR 语言资源](https://learn.microsoft.com/en-us/uwp/api/windows.media.ocr.ocrengine.availablerecognizerlanguages)。

`resources/ocr/` 为后续独立 OCR 模型预留；当前无须在其中下载模型。Windows OCR 对未打包身份的桌面应用存在官方支持范围限制；当前构建已作实机验证，仍需在其他目标 Windows 版本验收，后续可替换为独立 ONNX 引擎。

## 字典与日语读音

- 英语：从 [ECDICT](https://github.com/skywind3000/ECDICT) 的 `ecdict.csv` 导入 **770,611 条**有释义词条到 SQLite。包含中文/英文释义、音标和 exchange 词形表；先精确匹配，再查词形表和规则候选。缺中文时明确标为“英文释义”。词库导入为开发阶段独立步骤，程序运行不下载数据。
- 日语：SQLite 测试词库 **10 条**，SudachiPy + SudachiDict-core 提供分词、原形、词性及假名读音。逐 token 的 `surface / reading / dictionary_form / part_of_speech` 保留在结果对象中。
- 单元测试仍使用 `resources/dictionaries/*.demo.json` 的小型词库。发行构建会检查英语词库至少 50 万条，避免再次误发演示词库。JMdict 尚未接入。
- 开发时使用已安装的 Sudachi 字典；打包脚本将其复制到 `resources/sudachi/system.dic`。如该路径存在，优先使用该本地字典。
- 词典数据库采用 `entries(headword, reading, phonetic, part_of_speech, meaning)` 和 `forms(form, headword)` 两张表，`headword`、`form` 为主键。未来导入器应在运行前将 ECDICT / JMdict 转成此结构；禁止运行时解析完整 XML。

短语和句子由 resources/translation 中的离线模型翻译，CPU 推理，不依赖在线接口。只有开发环境未装模型时才回退为逐词释义，并明确标注不是整句翻译。

### 可选日语模型的安装与迁移

在了解并接受 [模型许可](https://huggingface.co/LiquidAI/LFM2-350M-ENJP-MT-GGUF/blob/main/LICENSE) 后，可安装较新的日语模型：

```powershell
.\.venv\Scripts\python.exe scripts/install_japanese_model.py
```

安装脚本从固定版本下载并校验官方 GGUF 权重和官方 llama.cpp Windows CPU 运行文件，保存到 `resources/translation/ja_en_lfm/`。运行时调用本地隐藏进程，并强制使用离线模式，不启动 HTTP 服务，不需要安装 PyTorch、Ollama 或模型仓库的 Python 代码。资源完整时优先使用此模型；未安装时兼容原有 Argos 日英模型。模型运行出错会明确提示。

两台电脑迁移时复制整个 `resources/translation/ja_en_lfm/`，包括 `runtime/`、元数据、来源记录和许可；同时保留 `resources/translation/en_zh/`。或者在第二台电脑运行上述安装脚本重新下载。权重和运行程序不上传 GitHub，安装脚本和代码会同步。打包时仅包含选中的模型；失败候选及 PyTorch 测试环境不进入发行包。

## 配置与数据

首次运行自动创建 `config.json`，可参考 `config.example.json`。无效配置会报告错误并临时使用默认值，保留原文件。

| 字段 | 默认 | 用途 |
| --- | --- | --- |
| `capture_hotkey` | `alt+q` | 支持 alt / ctrl / shift / win 加字母、数字或 F1–F24 |
| `popup_position` | `capture` | `capture` 截图区附近；`cursor` 鼠标附近 |
| `ocr_languages` | `["en", "ja"]` | 本地 OCR 语言 |
| `ocr_scale` | `2.0` | 放大倍率，1–4 |
| `theme` | `light` | `light` / `dark` |
| `log_ocr_text` | `false` | 是否将识别原文写入日志 |

托盘设置修改后即时生效；直接编辑配置文件后需重启。历史按“语言 + 词典原形（或规范化原文）”合并计数，包含预留的书名、上下文、同步和掌握状态字段。日志使用轮转文件，位于 `logs/grepzztranslate.log`。

## 项目结构

```text
GrepzzTranslate/
├─ src/grepzztranslate/
│  ├─ main.py / app.py      入口、托盘与流程协调
│  ├─ hotkey.py             Windows 全局快捷键
│  ├─ capture.py            分屏 Overlay 与高 DPI 截图合成
│  ├─ ocr.py                本地 OCR、预处理
│  ├─ language.py           规范化、语言检测、词形与读音
│  ├─ dictionary.py         本地 SQLite 字典
│  ├─ lookup.py / models.py 查询结果与业务流程
│  ├─ ui.py / worker.py     浮窗、设置、后台工作线程
│  ├─ storage.py            查询历史
│  └─ config.py / paths.py / resources.py / services.py
├─ resources/dictionaries/ 测试源数据与生成的词库
├─ data/                   个人历史，不进 Git
├─ logs/                   运行日志，不进 Git
├─ scripts/                词库生成、阅读测试页、打包
├─ tests/                  业务、UI、坐标、真实 OCR 测试
├─ GrepzzTranslate.spec
├─ config.example.json
└─ run.py
```

## 测试与打包

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run.py --self-test
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
.\.venv\Scripts\python.exe scripts/package_release.py
```

测试中的真实 OCR 用例要求 Windows 英日 OCR 资源；界面测试需要可用的桌面会话。跨 DPI 测试使用合成的显示器数据，不能替代真实多屏验收。

`--self-test` 会显示本地测试文字，使用真实屏幕截图、Qt 框选测试事件、后台 OCR 与查询完成英日验收，并验证 Esc 后程序仍在后台。报告在 `logs/self-test.json`，结果浮窗截图在 `logs/self-test-popup-*.png`。测试查询使用独立的 `data/self-test-history.db`。运行前请退出同一程序的其他实例，避免快捷键冲突。打包版也支持 `GrepzzTranslate.exe --self-test`。该验收不会发送物理键盘 Alt+Q，仍需按前面的手工步骤检查全局按键。

`requirements.lock.txt` 记录本次实际验证的依赖版本。需要复现环境时，先安装该文件，再执行 `pip install --no-deps -e .`。

推荐执行 `scripts/build.ps1` 完成 PyInstaller 构建及外置资源复制；单独运行 `.spec` 不会执行后续外置资源复制步骤。

```text
dist/GrepzzTranslate/
├─ GrepzzTranslate.exe
├─ _internal/
├─ resources/
│  ├─ dictionaries/english.db、japanese.db
│  └─ sudachi/system.dic
├─ data/
├─ config.json
├─ README.md
└─ THIRD_PARTY_NOTICES.md
```

将整个 `dist/GrepzzTranslate` 目录压缩 / 复制到另一台 Windows x64 电脑，解压到可写目录，双击 `GrepzzTranslate.exe`。不需要 Python、Visual Studio 或 IDE。不要仅复制 exe。目标系统仍需英日 Windows OCR 资源；系统组件兼容性和不同 Windows 版本需实际验收。

升级时保留个人 `data/` 和 `config.json`。构建脚本在 `build/package/` 生成程序，再更新发行目录，保留既有历史和设置。ZIP 打包脚本排除历史和日志，并使用默认配置。

## 当前限制

- 英语词库仍可能缺少新词、专名和特定短语。日语释义仍只有 10 个演示词条，读音覆盖范围由 Sudachi 决定。
- Unicode 语言检测是启发式，纯中文汉字会被视为 Japanese；混合语言及 OCR 引擎结果选择可能误判。
- 已有本地机器翻译；已有词级 Ruby 注音；无 TTS、账号、同步、自动更新或历史管理界面。
- 旋转文字、竖排日语、低对比度、复杂背景和极小文字可能识别不准。
- 每个显示器独立显示 Overlay，按 Qt 全局逻辑坐标合成截图。覆盖负坐标和混合缩放的自动测试；真实多屏、不同缩放比、HDR 仍需更多设备验证。
- 受保护的视频、某些游戏独占全屏、管理员权限界面、锁屏可能不能捕获。
- 程序必须放在可写目录；不推荐直接放在 Program Files。历史数据库未加密。
- 安装包尚未签名；尚未在另一台干净 Windows 电脑做完整验收。

## Roadmap

| 版本 | 范围 |
| --- | --- |
| v0.1 | Alt+Q、截图框选、Windows 本地 OCR、测试英日词典、Sudachi 读音、SQLite 历史、浮窗和托盘 |
| v0.1.1 | ECDICT 英语词库、逐词释义、OCR 原文修正、清晰错误提示、安全更新个人数据 |
| v0.1.3 | 点击外部自动收起、迟到结果抑制、浅色阅读卡片与按需 OCR 修正 |
| v0.1.4–0.1.5 | 已实现离线整句翻译与日语词级 Ruby 注音 |
| v0.2 | JMdict 导入、词形优化、注音质量优化 |
| v0.3 | 本地 TTS、英语与日语发音 |
| v0.4 | OCR 优化、复杂 PDF、高 DPI 和多屏实机覆盖 |
| v0.5 | 更高质量本地模型、上下文解释 |
| v0.6 | 用户选择启用的 Google Sheets 同步 |

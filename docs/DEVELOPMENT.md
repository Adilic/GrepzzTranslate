# 双机开发与项目理解手册

本项目是 Windows 桌面应用。“部署开发环境”指每台电脑分别准备 Python、依赖、词库、模型和系统 OCR；不是部署到服务器。两台电脑通过 GitHub 同步源码，运行环境与个人数据各自独立。

## 1. 先理解这四层

| 层 | 包含内容 | 如何到第二台电脑 |
| --- | --- | --- |
| 源码 | src、scripts、tests、配置示例、文档、依赖清单 | Git clone / pull |
| Python 环境 | .venv、PySide6、Sudachi、推理运行库 | 每台电脑重新安装，不复制 .venv |
| 数据资源 | 英语 SQLite 词库、日语词库与 Sudachi 字典、离线模型 | 安装脚本下载生成，或复制资源以节省下载 |
| 系统与个人数据 | Windows OCR、config.json、data、logs | OCR 每台安装；设置和历史按需单独迁移 |

GitHub 是源码的共同版本来源。push 上传已提交的代码，pull 获取代码；这两个操作不会安装 Python、下载模型或更新已经打包的 exe。

## 2. 第二台电脑首次准备

要求 Windows 10/11 x64、Git、Python 3.12 x64（安装时保留 py 启动器）。不要求 Visual Studio。首次安装需要联网。仓库地址： https://github.com/Adilic/GrepzzTranslate 。

在希望存放项目的位置打开 PowerShell：

```powershell
git clone https://github.com/Adilic/GrepzzTranslate.git
cd GrepzzTranslate
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
```

setup-dev 会创建本机 .venv、按锁定版本安装依赖、把项目作为可编辑包安装、准备词库和模型，最后实际测试模型推理及 Windows OCR。已有的完整资源会复用，不改写个人配置、历史，也不自动修改系统 OCR 设置。中途失败可修复原因后重跑。

缺少 OCR 时，在第二台电脑的管理员 PowerShell 中按需执行：

```powershell
Add-WindowsCapability -Online -Name 'Language.OCR~~~en-US~0.0.1.0'
Add-WindowsCapability -Online -Name 'Language.OCR~~~ja-JP~0.0.1.0'
```

再回到项目目录检查和运行：

```powershell
.\.venv\Scripts\python.exe scripts/check-dev.py
.\.venv\Scripts\python.exe run.py
```

若安装的是 GitHub 私有仓库，Git 操作需要登录有权限的账号。GitHub 浏览器登录与命令行凭据不是同一件事；不要把访问令牌写进代码或仓库地址。

## 3. 不想在另一台电脑重新下载资源

从当前项目根目录复制这些文件到第二台克隆目录的相同位置：

- resources/dictionaries/english.db、japanese.db
- 整个 resources/translation/（包含模型、分词器、metadata 和来源说明）
- 可选：data/downloads/ecdict.csv、build/model-downloads/，仅用于以后重新生成资源。

然后仍然执行 setup-dev.ps1；它会安装第二台电脑自己的 Python 依赖，并复用上述完整资源。Sudachi 字典通过 Python 依赖安装，开发时无须从发行包搬出 system.dic。Windows OCR 必须在第二台电脑安装。

`-SkipDownloads` 可跳过词库和模型下载，但不是完全离线安装：pip 仍可能联网，最终检查也会报告缺失资源。不要复制 .venv、build 中的程序或本机 .lnk 快捷方式来替代开发安装。

## 4. 每天在两台电脑之间接力

开始工作前：

```powershell
git status
git pull --ff-only
```

只在工作区干净时拉取。若有未完成修改，先提交保存，或暂存后再拉取。尽量完成一台电脑的提交和推送后，再去另一台继续同一部分工作。

修改代码后运行相关测试；交接时：

```powershell
git diff
git add src scripts tests docs README.md
git commit -m "说明本次改动"
git push
```

add 的路径应按实际修改调整。首次提交可能需要在每台仓库配置姓名和 GitHub 隐私邮箱：`git config user.name "你的名字"`、`git config user.email "GitHub 设置中的隐私邮箱"`。这些是本机 Git 配置，不跟随源码同步。

若两台电脑都产生了新提交，`pull --ff-only` 会停止，避免自动产生你不理解的合并。先保存本地工作，再 fetch，检查差异后 merge 或 rebase；不要用强制 push 或 hard reset 草率覆盖另一台工作。可以把具体提示交给助手处理。

依赖清单改变后重跑 setup-dev.ps1；只是改 Python 代码，一般重启源码程序即可生效。若修改了资源版本，按更新说明重新运行资源安装脚本，setup-dev 不会主动替换已经存在的完整模型。

## 5. 一次截图怎样变成结果

```text
run.py → main.py → ApplicationController
Alt+Q → hotkey.py → capture.py 截图框选
→ worker.py 后台线程 → ocr.py Windows 本地识别
→ lookup.py 判断语言并组织结果
   英语：dictionary.py 查询 ECDICT，必要时 translation.py 离线翻译
   日语：language.py 用 Sudachi 分词与注音，查词或离线翻译
→ models.py LookupResult → ui.py 浮窗 / furigana.py 汉字上方假名
→ storage.py 保存本机历史
点击外部 → outside_click.py → 隐藏浮窗，后台继续运行
```

截图识别、读音、翻译是三件不同的事：OCR 错一个汉字，后续注音和译文都可能错；读音由 Sudachi 提供，不是翻译模型生成。日语机器翻译通过日→英→中，不能把它当成精确词典。日语 SQLite 只有少量演示释义，不代表只能注音这些词。

Qt 主线程负责界面和快捷键，QThread 中的 worker 负责 OCR 和查询。请求编号用于防止关闭浮窗后旧结果重新出现。查词模型延迟加载并复用，实际运行不访问翻译服务。

## 6. 建议的读代码顺序与练习

1. 阅读 config.py、models.py：弄清输入配置和结果有哪些字段。
2. 阅读 main.py、app.py：理解启动、后台常驻、信号、请求状态。
3. 阅读 capture.py、ocr.py：理解像素、缩放和识别出的原文。
4. 阅读 lookup.py、language.py、translation.py：分清词典、注音和翻译的职责。
5. 阅读 ui.py、furigana.py：理解结果怎样排版、换行和关闭。
6. 对照 tests 阅读；先在新分支改一个浮窗提示并从源码启动，再练习添加一个注音回归测试，最后进行一次完整打包。

排错时顺着上述链路定位，不要把“识别正确但没有词条”与“根本没识别出文字”混为一谈。

## 7. 测试、源码运行与打包

开发时先退出托盘里正在运行的发行版，避免 Alt+Q 被占用。

```powershell
.\.venv\Scripts\python.exe scripts/check-dev.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run.py --self-test
```

check-dev 验证资源及运行库；pytest 验证逻辑、真实 OCR 与模型；self-test 显示测试页进行屏幕截图，验证浮窗和结果。桌面测试串行运行，保持测试文字可见；输入法候选框、其他窗口可能遮挡截图。自动测试不是不同硬件、真实多屏和真实按键操作的全部保证。

需要独立 exe 时：

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
.\.venv\Scripts\python.exe scripts/package_release.py
```

输出到 dist。不要只运行 PyInstaller spec：完整打包脚本还负责复制词库、模型和许可证。修改源码后旧 exe 不会自动更新，必须重新打包。源码的 config/data/logs 位于项目根目录，发行版的这些文件位于 dist/GrepzzTranslate，各自独立。

## 8. 常见问题对照

| 现象 | 优先检查 |
| --- | --- |
| pull 后 exe 没变化 | 运行的是旧发行版；启动 run.py 或重新打包 |
| 缺 Python 模块 | 是否使用本项目 .venv；重跑 setup-dev |
| 英语只能识别却查不到 | check-dev 的英语词库数量；OCR 原文是否正确 |
| 无整句翻译 | resources/translation 是否完整；check-dev 能否实际推理 |
| 无日语注音 | OCR 是否判为日语；Sudachi 是否正常；结果 tokens/reading 是否保留 |
| 快捷键失效 | 两个版本是否同时启动；托盘设置有无注册冲突 |
| 缺少 OCR | 安装 Windows 英日 OCR 后重启程序或托盘重新加载 |
| 推送被拒绝 | 账号权限、远端是否有另一台的新提交；不要强制覆盖 |

## 9. 不应随着 Git 同步的内容

.gitignore 排除了环境、模型、构建产物、个人配置、历史、日志和快捷方式。Git 同步不是整盘备份。个人历史如要迁移，先关闭程序再复制对应 data/history.db；不要把两台数据库直接覆盖当作合并。默认日志不保存 OCR 原文，历史则会保存查询内容。

当前电脑验证通过，不等于第二台已验证。第二台完成环境检查、测试、Alt+Q 实际框选、外部点击收起，以及日语注音后，才算该电脑部署完成。

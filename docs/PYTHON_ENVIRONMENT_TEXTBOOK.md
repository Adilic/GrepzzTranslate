# 从零理解 Python 环境、项目结构与双机迁移

> 如果希望学习适用于其他 Python 项目的通用原理，请优先阅读新的 [三册 Python 工程教材](python-course/README.md)。本篇保留为 GrepzzTranslate 的入门案例说明。

以 GrepzzTranslate 为贯穿案例 · Windows / PowerShell · 2026-10-04

这份教材面向刚接触开发的人。目标不是让你背下安装命令，而是让你能回答：程序在哪里、谁在运行它、依赖装到了哪里、哪些文件应该同步，以及第二台电脑缺了什么。

这里的“完整”指覆盖本项目开发环境的完整生命周期，不是涵盖 Python 语言的所有语法。可以暂时不学类、异步、算法，就先把环境和迁移弄明白。

## 怎么学习

建议分六次，每次约 30–45 分钟；时间只是建议，不用赶进度。

| 次数 | 阅读内容 | 学完应能解释 |
| --- | --- | --- |
| 第一次 | 第 1–3 章 | Python、终端、路径、解释器分别是什么 |
| 第二次 | 第 4–5 章 | .venv、激活、pip、依赖版本是什么 |
| 第三次 | 第 6–7 章 | 项目文件各有什么用，源码怎样运行 |
| 第四次 | 第 8–9 章 | 哪些文件走 Git，另一台怎么恢复环境 |
| 第五次 | 第 10–11 章 | 修改、测试、打包与故障定位 |
| 第六次 | 第 12 章及附录 | 完成小实验，用自己的话复述完整流程 |

不要一次执行整本教材的命令。标为“观察”的命令不会安装东西；标为“安装／修改”的命令会改变环境。已有正常运行的项目不需要为了学习重复安装或删除环境。

---

## 第 1 章：程序能运行，靠的不只是代码

### 1.1 先分清五件东西

| 概念 | 解释 | 项目实例 |
| --- | --- | --- |
| 源码 | 我们写下的程序指令，通常是文本文件 | src/grepzztranslate/ui.py |
| 解释器 | 读取并执行 Python 程序的软件 | python.exe |
| 依赖包 | 其他开发者写好的、供程序使用的功能 | PySide6、SudachiPy |
| 资源文件 | 程序处理数据时需要读取的内容 | 词库、翻译模型 |
| 系统能力 | 由 Windows 提供的能力 | Windows OCR、全局快捷键 |

拿到一个 ui.py，不意味着电脑自动知道怎么运行它；安装 Python，也不意味着所有依赖和模型自动齐全。

GrepzzTranslate 要运行，需要这些部分协同：

```text
你的代码
   ↓ 由它执行
Python 解释器
   ↓ 导入所需功能
依赖包：界面、日语处理、翻译推理
   ↓ 读取或调用
词库、模型、Windows OCR
   ↓
屏幕上出现结果浮窗
```

### 1.2 “开发环境”到底包括什么

它是开发、运行和验证项目所需条件的集合。狭义 Python 环境主要指解释器和依赖；完整项目开发环境还包含源码、工具、数据资源和系统条件。

编辑器负责帮你看和改代码，终端负责接收命令，Git 负责版本管理；它们都不是 Python 解释器。即使没有编辑器，也能从终端运行项目。

**练习 1**：第二台电脑有项目源码、有 Python，却报“找不到 PySide6”。缺的是哪一层？

---

## 第 2 章：文件、文件夹、路径和终端

### 2.1 项目根目录

“根目录”在这里指项目最外层文件夹，不是 Windows 的 C 盘根目录。当前项目根目录是：

```text
C:\Users\zhouq\Desktop\GrepzzTranslate
```

第二台可以放在 `D:\Projects\GrepzzTranslate`。源码不应该要求两台电脑使用同一个用户名和绝对路径。

### 2.2 绝对路径与相对路径

绝对路径包含完整位置；相对路径需要结合“当前目录”理解。

```text
C:\Users\zhouq\Desktop\GrepzzTranslate\run.py   绝对路径
.\run.py                                      当前目录下的文件
.\.venv\Scripts\python.exe                   当前目录下的 Python 入口
..\                                           上一级目录
```

`.` 是当前目录，`..` 是上一级目录。`.venv` 则是一个完整的文件夹名字，不能把其中的点当成单独的 `.`。

文件夹名字以点开头是一种常见约定；在 Windows 中，这不等于一定带有“隐藏文件”属性。

### 2.3 PowerShell 是什么

PowerShell 是解释命令的 shell。Windows Terminal 是可以承载 PowerShell 等 shell 的终端窗口。你输入命令，shell 按照规则找到程序并传递参数。

观察命令：

```powershell
Get-Location
Get-ChildItem
```

第一条显示你当前在哪里，第二条列出当前目录的内容。

进入项目目录：

```powershell
cd C:\Users\zhouq\Desktop\GrepzzTranslate
```

有空格的路径需要引号，例如 `cd "D:\My Projects\GrepzzTranslate"`。路径要换成你电脑上实际存在的位置。

终端里的 `PS C:\...>` 是提示符，不属于命令；复制教程时不用复制它。

### 2.4 为什么在错误目录执行会失败

若当前目录是桌面，`python run.py` 寻找的是桌面上的 run.py，不会自动知道你想运行哪个项目。

本项目查找资源时会根据源码或 exe 的位置计算项目目录，尽量不依赖当前目录；但是你输入的相对命令路径仍依赖当前目录。这两件事要分开。

**练习 2**：你在 `D:\Projects`，而项目在 `D:\Projects\GrepzzTranslate`。执行 `.\.venv\Scripts\python.exe` 为什么找不到？先执行什么命令？

---

## 第 3 章：Python、python.exe 和 py 的区别

### 3.1 Python 有语言和软件两层含义

“用 Python 写代码”中的 Python 是语言；“电脑安装 Python 3.12”中的 Python 通常指包含解释器和标准库的软件发行版。

`python.exe` 是实际运行程序的入口。标准库是随 Python 提供的常用模块，例如 pathlib、json、sqlite3；通常不用额外 pip 安装它们。

第三方包则另行安装，例如 PySide6。

### 3.2 一台电脑可以有多个 Python

例如电脑上同时存在 Python 3.12、另一个工具自带的 Python，以及几个项目的虚拟环境。

所以“我已经安装过这个包”还不够，要问：**装进哪个 Python 环境了？当前又是哪个 Python 在运行？**

观察当前命令能找到什么：

```powershell
Get-Command python -All
```

Windows 的 `py` 是 Python 启动器／管理入口，不是项目依赖。配置了相应启动器时，`py -3.12` 表示选择已安装的 Python 3.12。它不会因为你写了 3.12 就保证电脑已经有对应解释器。

### 3.3 先学最可靠的观察方法

在项目根目录执行：

```powershell
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
```

第一条显示版本；第二条显示实际解释器入口的路径。`-c` 表示直接执行后面引号里的简短 Python 代码。

这个项目的推荐开发基线是 **Windows x64 + Python 3.12 x64**。虽然项目声明允许更高 Python 版本，也不代表所有依赖都已在每个新版本验证。

**练习 3**：系统 `python` 是 3.13，但 `.venv\Scripts\python.exe` 是 3.12。用完整的 `.venv` 路径运行时，实际使用哪个版本？

---

## 第 4 章：真正理解 .venv

### 4.1 venv 与 .venv 不是同一个东西

- `venv`：Python 自带的创建虚拟环境的工具模块。
- `.venv`：我们给创建出来的环境文件夹起的名字。

名字可以改成别的，但本项目脚本约定使用 `.venv`，所以不要随意改名。

创建命令（安装／修改操作；已有环境时不用重复练习）：

```powershell
py -3.12 -m venv .venv
```

逐段解释：

| 片段 | 意思 |
| --- | --- |
| py -3.12 | 选择 Python 3.12 |
| -m venv | 用这个 Python 运行 venv 模块 |
| .venv | 把新环境放在当前目录的 .venv 文件夹 |

### 4.2 它里面大致有什么

```text
.venv/
├─ pyvenv.cfg          记录环境与基础 Python 的关系
├─ Scripts/
│  ├─ python.exe       这个环境的 Python 入口
│  ├─ pip.exe          依赖安装工具入口
│  └─ Activate.ps1     激活脚本
└─ Lib/
   └─ site-packages/   这个环境安装的第三方包
```

虚拟环境不是虚拟机，也不是安全沙箱。它主要隔离 Python 包；程序仍可以访问你账号有权限访问的文件和网络，也仍使用 Windows 的能力。

它通常还依赖创建它的基础 Python 安装，不是完全独立的便携 Python 副本。不要看到里面有 python.exe，就以为卸载基础 Python 永远不会影响它。[Python 官方 venv 说明](https://docs.python.org/3.12/library/venv.html)

观察环境与基础安装：

```powershell
.\.venv\Scripts\python.exe -c "import sys; print('环境:', sys.prefix); print('基础:', sys.base_prefix)"
```

常规 venv 中，两者不同表示正在虚拟环境里运行。

### 4.3 为什么每个项目各建一个

项目 A 需要某个库的旧版，项目 B 需要新版。分开的环境让依赖各自安装，降低互相干扰的机会。[Python 官方入门教程](https://docs.python.org/3.12/tutorial/venv.html)

```text
基础 Python 3.12
├─ GrepzzTranslate/.venv：本项目所需依赖
└─ AnotherProject/.venv：另一个项目所需依赖
```

新建环境不会自动装好本项目的所有依赖，也不会自动下载翻译模型。

### 4.4 “激活”做了什么

```powershell
.\.venv\Scripts\Activate.ps1
```

激活主要调整当前终端会话的环境变量，使 `python` 等命令优先找到 `.venv\Scripts` 下的入口。`PATH` 就是 shell 查找程序时参考的一组目录。

激活不会重新安装依赖，也不会启动 GrepzzTranslate。通常只影响当前终端及它启动的子进程；打开新终端需要重新选择环境。

激活后可以写：

```powershell
python run.py
```

退出激活状态用 `deactivate`，这不删除环境，也不卸载依赖。

### 4.5 不激活能不能运行？能

```powershell
.\.venv\Scripts\python.exe run.py
```

完整指定入口就不需要激活。初学阶段，本教材优先采用这种方式，避免“以为激活了，实际用了别的 Python”。激活脚本被 PowerShell 策略阻止时，也可以直接使用这种方式，无须为了运行程序改全局执行策略。

### 4.6 为什么不把 .venv 复制到第二台

里面的配置和脚本可能引用原电脑路径，也与基础解释器、平台有关。官方将虚拟环境视为应当重建的环境，而非搬运的成品。[官方说明](https://docs.python.org/3.12/library/venv.html)

你要迁移的是“创建环境的配方”，而不是原封不动搬走环境文件夹：

```text
同一份源码 + Python 版本要求 + 依赖清单 + 资源准备脚本
                         ↓
              在第二台电脑重建 .venv
```

**练习 4**：激活环境后关闭终端，依赖会消失吗？下次用完整 `.venv` 路径运行，还要激活吗？

---

## 第 5 章：pip、依赖与版本清单

### 5.1 pip 管什么，不管什么

pip 主要安装 Python 发行包。它不会替你同步源码、配置 GitHub，或安装 Windows OCR 系统组件。

使用这个环境自己的 pip：

```powershell
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe -m pip list
.\.venv\Scripts\python.exe -m pip show PySide6
```

`-m pip` 的意思是“让指定的 Python 运行 pip 模块”。比单独写 `pip` 更容易明确安装目标。[Python Packaging 安装指南](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)

`pip show` 中的 Location 能帮助你确认包是否装在当前项目的 site-packages。

### 5.2 依赖为什么还带着其他依赖

直接依赖是我们明确使用的库，例如 CTranslate2；间接依赖是这些库运行时需要的其他库。pip 通常会一并解析、安装它们。

安装名和 Python 导入名也不一定相同。例如安装 SudachiPy，代码使用 `import sudachipy`。不能只凭名字大小写和连字符猜包的使用方式。

### 5.3 三份文件的区别

| 文件 | 本项目中的角色 | 例子 |
| --- | --- | --- |
| pyproject.toml | 项目元数据、依赖范围、开发依赖和打包配置 | PySide6>=6.8,<7 |
| requirements.txt | 开发安装的简短入口 | -e .[dev] |
| requirements.lock.txt | 已验证环境的具体依赖版本清单 | PySide6==6.11.2 |

`>=6.8,<7` 表示一个允许范围，`==6.11.2` 表示具体版本。两台电脑若安装范围依赖的时间不同，可能得到不同版本，所以复现时优先用具体版本清单。

本项目的 `.lock.txt` 仍是 pip requirements 格式；文件名中有 lock 不代表 pip 自动把它当作特殊锁文件。它没有覆盖操作系统、Python 安装、模型版本和所有系统动态库，也不是带完整校验哈希的跨平台环境快照。

### 5.4 “安装我们自己的项目”是什么意思

```powershell
.\.venv\Scripts\python.exe -m pip install --no-deps -e .
```

- `.`：当前目录这个项目。
- `-e`：可编辑安装，让环境能导入开发目录中的代码。
- `--no-deps`：不在这一步重新解析依赖，前提是依赖已经按清单安装。

项目代码放在 src/grepzztranslate，而不是直接位于根目录。可编辑安装让 Python 能找到它；普通源码修改后，重启程序就能使用修改后的代码。不应去 site-packages 里改我们的源码。

### 5.5 wheel 是什么

`.whl` 是 Python 包的一种安装格式；可能包含纯 Python 代码，也可能包含针对某个平台编译好的组件。`--only-binary=:all:` 要求 pip 使用 wheel，不从源码编译依赖。如果没有兼容 wheel，安装会失败，需要检查 Python 版本、平台和依赖版本，而不是立即安装一堆编译工具。[包安装说明](https://packaging.python.org/en/latest/tutorials/installing-packages/)

### 5.6 pip freeze 的用处与局限

`pip freeze` 输出当前环境里的已安装依赖记录。它可能混入临时安装的包、本机路径、可编辑安装信息；不要每次随手覆盖项目的依赖清单。

本项目曾出现把 `C:\Users\zhouq\...` 写进清单的问题，已修正。依赖清单应该能被另一台电脑理解，不应依赖你的个人目录。

**练习 5**：包明明装好了，却报 ModuleNotFoundError。你首先检查哪两条路径？

---

## 第 6 章：读懂 GrepzzTranslate 的文件结构

```text
GrepzzTranslate/
├─ .git/                   Git 提交历史、分支和远端配置
├─ .venv/                  本机 Python 环境
├─ src/grepzztranslate/    应用源码
├─ scripts/               安装、检查、构建等辅助程序
├─ tests/                 自动测试
├─ docs/                  教材和开发手册
├─ resources/             词库、模型、来源说明
├─ data/                  本机查询历史等数据
├─ logs/                  本机运行日志
├─ build/                 构建过程中的中间文件
├─ dist/                  打包后的独立程序与 ZIP
├─ run.py                 源码运行入口
├─ pyproject.toml          项目和依赖声明
├─ requirements.lock.txt  验证过的依赖版本
├─ config.example.json    可共享的默认配置示例
├─ config.json            当前电脑实际使用的配置
├─ .gitignore             告诉 Git 忽略哪些文件
└─ README.md              项目总说明
```

### 6.1 各种后缀代表什么

| 后缀 | 用途 | 是否一般直接编辑 |
| --- | --- | --- |
| .py | Python 源码 | 开发时编辑 |
| .ps1 | PowerShell 脚本 | 理解后编辑 |
| .md | Markdown 文档 | 可以编辑 |
| .json / .toml | 结构化配置 | 按格式编辑 |
| .db | SQLite 数据库 | 不当文本编辑 |
| .bin / .model | 模型权重、分词器等资源 | 不手工编辑 |
| .exe / .dll | 程序入口、动态库 | 不当源码编辑 |
| .lnk | Windows 快捷方式 | 可能引用本机路径 |

### 6.2 包、模块与 import

一个 `.py` 文件通常可以成为一个模块；多个模块可以组织成包。本项目包名是 `grepzztranslate`。

```python
from grepzztranslate.ocr import OCRService
```

这句话表示从对应模块中导入 OCRService，不是从互联网下载程序。导入需要的包没有安装，或者 Python 找不到源码位置，就可能失败。

### 6.3 哪些东西不应手工修改

通常不改 `.venv` 内部的包，也不改 build、dist 中复制出来的源码或运行库。修复应落在 src、scripts、配置或测试里；再重新运行或打包。

`__pycache__`、`.pyc` 是运行时生成的缓存，不是你应该编辑的源码。它们通常不进 Git。

`.env` 与 `.venv` 也不同：`.env` 常用来放环境变量配置，本项目当前不依赖它；`.venv` 是 Python 环境目录。

**练习 6**：你想调整浮窗的字体，应该找 src 中的界面代码，还是修改 dist 里的文件？为什么？

---

## 第 7 章：从启动到翻译，哪些部分在工作

### 7.1 源码运行入口

```powershell
.\.venv\Scripts\python.exe run.py
```

run.py 加载主程序，主程序读取配置、检查单实例锁，创建界面与后台工作线程，注册快捷键。

程序会驻留托盘。关掉浮窗不等于退出进程；右键托盘退出才是正常退出应用的方式。

### 7.2 核心模块的分工

| 文件 | 主要负责 |
| --- | --- |
| main.py | 启动、日志、配置、单实例 |
| app.py | 协调界面、快捷键、后台请求与退出 |
| hotkey.py / capture.py | 快捷键和屏幕框选 |
| worker.py | 在后台执行识别与查询 |
| ocr.py | 调用 Windows OCR，处理识别结果 |
| lookup.py | 根据语言组织查词、注音和翻译 |
| language.py | 语言判断、词形和 Sudachi 日语分析 |
| translation.py | 加载本地模型并推理 |
| ui.py / furigana.py | 结果浮窗与汉字上方注音 |
| storage.py / paths.py | 历史存储和资源路径 |

### 7.3 三个容易混淆的步骤

1. **OCR**：图片变文字，例如识别出「本書」。
2. **注音**：为日语文字分析读音，例如「ほんしょ」。
3. **翻译**：把日语内容转换为中文。

这三步不是同一个模型。注音不能修复全部 OCR 误字，翻译正确也不保证读音正确。

本项目的英语有约 77 万条词库；日语 SQLite 只有少量演示释义，但 Sudachi 提供更广泛的读音，离线模型提供句子译文。

### 7.4 为什么既有 Python 依赖又有模型文件

CTranslate2 是执行推理的软件，模型权重是它读取的资源。安装运行库不等于安装模型，就像安装播放器不等于已经有电影文件。

Windows OCR 又是另一层系统组件，不在 .venv 里；所以搬走 Python 环境也无法替第二台安装 OCR。

**练习 7**：画面识别成了错误汉字，但注音符合那个错误汉字。最应该先查 OCR，还是更换翻译模型？

---

## 第 8 章：Git 同步什么，不同步什么

### 8.1 四个位置

```text
工作区：你正在编辑的文件
   ↓ git add
暂存区：准备纳入下一次提交的内容
   ↓ git commit
本地仓库：这台电脑的提交历史
   ↓ git push
GitHub：远端提交历史
```

文件保存、Git 提交、上传 GitHub 是三个不同动作。保存代码不等于 GitHub 已经收到；commit 成功也不等于另一台能看到。

`clone` 用于第一次取得仓库；`pull` 用于已有仓库后获取并整合远端更新。两者都不负责创建 .venv 或安装模型。

### 8.2 本项目实际同步边界

| 文件类别 | Git 同步 | 第二台怎样获得 |
| --- | --- | --- |
| 源码、测试、文档、脚本 | 是 | clone / pull |
| 依赖清单、配置示例 | 是 | clone / pull |
| .venv | 否 | 本机重新创建和安装 |
| 大型词库、翻译模型 | 否 | 脚本准备或复制资源 |
| 实际配置、历史、日志 | 否 | 各机独立，按需迁移 |
| 打包 exe、ZIP | 否 | 本机打包或另行传递发行包 |
| Windows OCR | 不属于仓库 | 系统安装 |

`.gitignore` 防止未跟踪文件被普通 add 纳入，但不会自动停止追踪已经提交的文件，也不会清除已有历史。

### 8.3 两台电脑不要各自凭记忆接力

先确保电脑 A 的工作已提交并推送，再让电脑 B 拉取。开始前查看 `git status`，工作区干净后再 `git pull --ff-only`。

如果两台都产生了不同的新提交，可能需要合并；不要直接 force push 覆盖。若有未保存到 Git 的工作，也不要随手 reset --hard。先看清差异，再处理。

GitHub 仓库公开不代表别人可以随意 push。拉取公共代码和向仓库写入所需的权限不同。每台机器的 Git 登录凭据也不由 clone 自动复制。

**练习 8**：电脑 A 已 commit，但没有 push。电脑 B pull 后没看到修改，是哪里还没完成？

---

## 第 9 章：完整迁移到第二台电脑

### 9.1 搬之前先确认目标

这里的目标是继续开发，不只是双击 exe。第二台需要：源码、Python 环境、词库模型、系统 OCR、Git 写入权限，以及通过验收的运行状态。

路径可以不同；环境要各自创建；个人数据不必强行相同。

### 9.2 推荐流程：重建，不复制整个磁盘目录

前提：安装 Git 和 Python 3.12 x64，并能使用 `py -3.12`。在计划存放项目的位置执行：

```powershell
git clone https://github.com/Adilic/GrepzzTranslate.git
cd GrepzzTranslate
powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1
```

最后一条启动单独的 Windows PowerShell 来执行项目脚本；此处的 Bypass 用于这个进程，不是设置永久全局策略。只运行你理解并信任的项目脚本。

setup-dev 做了这些事：

1. 没有 .venv 时，用 Python 3.12 创建。
2. 检查 Python 版本和 64 位架构。
3. 按锁定清单安装依赖，再以可编辑方式安装本项目。
4. 生成缺失的基础词库，必要时下载安装完整英语词库。
5. 必要时下载并安装翻译模型。
6. 执行环境检查，实际试运行英日翻译和日语注音，并检查 OCR 语言。

它不会自动安装 Windows 系统 OCR，也不会自动解决 GitHub 登录问题。安装失败时看具体错误，修复后可以重跑；已有完整资源会复用。

### 9.3 想节省下载，哪些可以复制

从电脑 A 的项目根目录复制到 B 的项目根目录相同相对位置：

```text
resources/dictionaries/english.db
resources/dictionaries/japanese.db
resources/translation/   整个目录
```

模型目录必须一起包含 model、sentencepiece.model、metadata 和来源说明，不要只复制 model.bin。复制完成后仍要运行安装脚本来创建 B 自己的 Python 环境。

可选缓存：`data/downloads/ecdict.csv` 和 `build/model-downloads/`。已有可用资源时，不需要为了运行再复制下载缓存。

`-SkipDownloads` 只跳过词库和模型下载，不会让整个 setup-dev 变成完全离线安装，因为 pip 仍可能需要联网。完全离线部署还需要预先准备兼容的 Python 安装器、所有依赖 wheel 及系统 OCR 安装来源，不属于简单复制这几个目录就能保证的事。

### 9.4 Windows OCR 单独准备

按开发手册安装英语与日语 OCR，之后重新检查。本项目不会为了安装 Python 依赖而要求管理员权限；安装 Windows 可选组件则可能需要管理员权限和系统下载。

OCR 的系统安装命令和路径见 [双机开发手册](DEVELOPMENT.md)。先学会区分系统组件与 Python 包，再执行相关安装步骤。

### 9.5 迁移个人数据时先确定来源

| 运行方式 | 配置和历史在哪里 |
| --- | --- |
| 源码 run.py | 项目根目录 config.json、data/history.db |
| 打包后的 exe | exe 同目录 config.json、data/history.db |

当前电脑若一直运行 dist/GrepzzTranslate/GrepzzTranslate.exe，真实使用历史位于发行目录里的 data，而不一定是项目根目录 data。

迁移前退出程序；如果目标电脑已有历史，覆盖不是合并，应先备份。日志通常无需搬，.lnk 可能指向原电脑路径，也无需直接搬。

### 9.6 验收，而不是“没有报错就算完成”

```powershell
.\.venv\Scripts\python.exe scripts/check-dev.py
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe run.py
```

最后手动确认 Alt+Q、框选英文单词、英文句子、日语注音、点击外部收起都正常。桌面测试与手工测试不要同时进行，其他窗口和输入法候选框可能遮挡测试文字。

截至教材编写时，脚本在当前电脑已验证，但没有在你的第二台电脑实际执行。因此不能提前声称另一台已经部署完成。

**练习 9**：clone 后目录比原电脑小很多，是代码丢了吗？列出三个通常被排除的大目录。

---

## 第 10 章：运行、开发、测试和打包的区别

### 10.1 四个动作不要混为一谈

| 动作 | 目的 | 对应操作 |
| --- | --- | --- |
| 安装环境 | 准备解释器、依赖和资源 | setup-dev.ps1 |
| 源码运行 | 执行当前开发代码 | python run.py |
| 测试 | 检查行为是否符合预期 | pytest、check-dev、自检 |
| 打包 | 制作不需要另装 Python 的发行目录 | build.ps1 |

打包不是把源码推送到 GitHub，也不是部署开发环境。Git pull 之后，旧 exe 不会自动包含新代码。

### 10.2 每天最短的开发循环

```text
确认 Git 状态 → 拉取更新 → 改源码 → 从源码启动
→ 验证改动 → 运行相关测试 → 提交 → 推送
```

编辑器如果提供 Python 解释器选项，选择当前项目 `.venv\Scripts\python.exe`。编辑器的运行按钮、调试器与终端可能各自有配置，出现差异时观察 sys.executable。

修改普通 Python 源码后，通常重启应用即可。修改依赖声明后需要重新安装；修改发行程序则需要重新打包。

源码版与 exe 同时运行可能争用 Alt+Q。测试前正常退出托盘中另一个版本。

### 10.3 打包后的东西是什么

```text
dist/GrepzzTranslate/
├─ GrepzzTranslate.exe
├─ _internal/       Python 运行组件和依赖
├─ resources/       词库、模型和许可说明
├─ config.json
└─ data/
```

这种发行方式需要整个目录，不是只有 exe；也不自动包含 Windows OCR 系统资源。具体构建和 ZIP 命令见开发手册，理解之后再执行。

**练习 10**：改了 src 下的代码，然后双击昨天的 exe，界面没变化。应该先重装 Python 吗？

---

## 第 11 章：排错时按顺序缩小范围

### 11.1 先问五个问题

1. 当前目录是什么？
2. 正在使用哪个 Python？
3. 包安装在那个 Python 的环境里吗？
4. 词库模型齐全吗？
5. Windows OCR 和快捷键是否可用？

观察命令汇总：

```powershell
Get-Location
Test-Path .\.venv\Scripts\python.exe
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip --version
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe scripts/check-dev.py
```

pip check 检查包声明的依赖关系，不等于测试模型推理、Windows OCR 或整个应用。

### 11.2 常见现象和正确的第一步

| 现象 | 第一项排查 |
| --- | --- |
| python 命令找不到 | Python 安装和 PATH；试明确解释器路径 |
| 找不到 run.py | 当前目录和文件路径 |
| ModuleNotFoundError | 解释器与安装依赖的环境是否一致 |
| No matching distribution found | Python 版本、系统架构、包版本及包源连接 |
| DLL load failed | 原生库、架构、运行组件；保留完整错误信息 |
| 找不到词库或模型 | 检查 resources，不要反复 pip install |
| 缺少 OCR 语言 | Windows 系统资源，不是 pip 包 |
| 同一词出现不同译文 | 先比较 OCR 原文，再比较模型版本和配置 |
| 另一台看不到代码修改 | A 是否 push，B 是否 pull，是否同一分支 |
| pull 后旧 exe 没变化 | 源码更新不等于 exe 更新 |

读 Python 错误时，最后一行通常给出异常类型与原因，上方调用栈帮助追踪来源。不要只截掉最后一行，也不要一遇到错误就删除所有环境重来。

### 11.3 应当保留与能够重建的区别

源码、个人历史、未提交修改不能随意删除。.venv 通常能按配方重建，但当前电脑若有未记入清单的新依赖，也要先记录。构建缓存一般可重建；模型要能重新下载或已有备份才适合清理。

本教材不提供一键删除目录的命令。初学阶段，先理解目录职责，再决定是否清理。

**练习 11**：`pip check` 通过，但模型目录不存在，翻译是否一定可用？为什么？

---

## 第 12 章：一个不改动正式项目的基础实验

目标：亲自看到“源码文件”和“执行它的环境”是两回事。不需要额外下载第三方包。

在你自己选择的学习目录中，新建一个独立文件夹（确认没有同名重要内容）：

```powershell
mkdir PythonEnvLesson
cd PythonEnvLesson
py -3.12 -m venv .venv
```

在该目录创建 `hello.py`，内容如下。用文本编辑器保存为 UTF-8，注意不是 hello.py.txt：

```python
import sys
from pathlib import Path

print("你好，这是环境观察实验")
print("实际解释器：", sys.executable)
print("当前工作目录：", Path.cwd())
print("脚本文件位置：", Path(__file__).resolve())
print("环境目录：", sys.prefix)
print("基础 Python：", sys.base_prefix)
```

运行：

```powershell
.\.venv\Scripts\python.exe hello.py
```

记录输出，再只修改第一句问候语并重新运行。你会看到：源码变了，无须重装 Python。

再在同一个 shell 中激活环境，确认 `python` 的实际路径：

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
deactivate
```

如果激活被策略阻止，跳过这一步；前面的明确路径运行已经证明可以使用环境。不要为了实验更改整台电脑的全局策略。

最后试着口头解释：hello.py 是内容，python.exe 是执行者，.venv 是项目环境；当前工作目录和脚本位置也不一定相同。

这项练习在教材中提供给你执行，本次编写没有替你创建或运行这个学习目录。

---

## 练习参考答案

1. 缺第三方依赖，或依赖装在另一个环境；先确认解释器再安装。
2. 路径指向 D:\Projects\.venv。应先 `cd GrepzzTranslate`，再执行项目中的命令。
3. 3.12，因为明确指定了 .venv 中的入口。
4. 依赖仍保存在磁盘。明确指定 .venv 路径运行无需激活。
5. sys.executable 显示的解释器路径，以及 `python -m pip show 包名` 中的安装位置。
6. 修改 src 中界面代码。dist 是已有构建结果，应由源码重新生成。
7. 先检查截图和 OCR 原文；注音可能只是正确处理了错误输入。
8. 缺少 push，修改还只在 A 的本地仓库。
9. 不一定丢文件；.venv、dist、resources/translation 等被排除。
10. 不需要。先从源码启动验证，想用新 exe 再重新打包。
11. 不一定。pip check 只检查 Python 包依赖，不检查外置模型是否存在。

## 自测：真正掌握的标志

不看教材，尝试解释以下六句话。如果某句讲不清，回看对应章节。

- “代码已经在 GitHub”不代表第二台环境已经齐全。
- “我装过这个包”不代表当前 Python 能导入它。
- 激活 .venv 是选择入口，不是启动程序，也不是重新安装。
- 两台电脑应分别创建环境，并尽量使用同样的版本配方。
- 模型文件、Python 依赖、Windows OCR 属于不同层。
- 修改源码、更新 GitHub、重新生成 exe 是三个不同动作。

## 一页速查

| 你要做什么 | 在项目根目录执行 |
| --- | --- |
| 看当前目录 | Get-Location |
| 看项目状态 | git status |
| 看实际 Python | .\.venv\Scripts\python.exe -c "import sys; print(sys.executable)" |
| 安装／检查开发环境 | powershell -ExecutionPolicy Bypass -File scripts/setup-dev.ps1 |
| 只检查完整环境 | .\.venv\Scripts\python.exe scripts/check-dev.py |
| 从源码启动 | .\.venv\Scripts\python.exe run.py |
| 跑自动测试 | .\.venv\Scripts\python.exe -m pytest -q |
| 查看改动 | git diff |
| 工作区干净时获取更新 | git pull --ff-only |

涉及 add、commit、push 的完整交接步骤见 [双机开发手册](DEVELOPMENT.md)。日常 Git 操作仍可以交给助手；掌握这些概念，是为了理解它正在做什么、能判断结果是否正确。

## 继续学习的官方资料

- [Python 3.12：虚拟环境与包入门](https://docs.python.org/3.12/tutorial/venv.html)：进一步理解环境隔离。
- [venv 模块说明](https://docs.python.org/3.12/library/venv.html)：创建、激活与可迁移性。
- [Python Packaging：使用 pip 与虚拟环境](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/)：依赖安装。
- [Python 包安装指南](https://packaging.python.org/en/latest/tutorials/installing-packages/)：版本约束、wheel、requirements。

先掌握本教材的概念与观察命令，再按开发手册实际部署。暂时不需要同时学习 Conda、Docker、Poetry 等更多工具；先把当前项目使用的 venv + pip + Git 流程弄清楚。

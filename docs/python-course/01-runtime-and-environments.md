# 第一册：计算机怎样找到并运行 Python

[课程目录](README.md) · [下一册](02-projects-and-reproducibility.md)

## 第 1 章：一次程序运行到底发生了什么

### 1.1 文件不是进程

磁盘上的 `hello.py` 是文件，它可以在电脑关机时一直存在。执行它时，操作系统启动 Python 进程；进程读取文件、分配内存、执行指令，然后退出。

所以同一个文件可以被多个进程运行。修改文件不一定改变已经运行的进程：它可能已经把代码和配置读入内存。长时间运行的服务、桌面程序通常要重启，除非明确实现了重新加载机制。

看见应用窗口关闭，也不能推断进程一定结束；有的程序继续在后台运行。反过来，命令行程序也可能没有图形窗口但正在工作。

### 1.2 从键盘输入到结果输出

假设输入：

```powershell
python report.py --month 10
```

可以分成六步理解：

1. 终端窗口把输入交给 shell。这里 shell 是 PowerShell。
2. PowerShell 解析命令、引号与参数，查找名为 python 的命令。
3. 找到解释器后，操作系统启动一个进程。
4. Python 根据参数找到 report.py，读取并执行它。
5. 程序再导入依赖、读取文件，向屏幕或文件输出结果。
6. 进程退出并返回退出码。约定上，0 通常表示成功，非 0 通常表示失败；最终含义由程序定义。

其中任一步出错，都可能被初学者笼统称为“Python 坏了”，但修复方法不同。

| 错误发生处 | 可能的提示 | 应关注什么 |
| --- | --- | --- |
| 找不到命令 | python 无法识别 | shell、PATH、解释器安装 |
| 找不到脚本 | can't open file | 工作目录、脚本路径 |
| 导入失败 | ModuleNotFoundError | 当前环境、导入路径、包名 |
| 读取资源失败 | FileNotFoundError | 程序访问了哪个文件 |
| 业务失败 | 输入不是合法月份 | 程序逻辑和输入数据 |

### 1.3 终端、shell、Python 交互模式

三者不是同一个东西：

- 终端是显示输入输出的界面，例如 Windows Terminal。
- shell 解析系统命令，例如 PowerShell、bash。
- Python 交互模式是 Python 启动后的输入环境，通常提示符是 `>>>`。

看到 `PS ...>` 时可以执行 `python -m pip ...`；看到 `>>>` 时是在输入 Python 代码。把安装命令写进 `>>>` 往往得到 SyntaxError，因为 Python 正尝试把系统命令当代码解析。

在 Python 交互模式输入 `exit()` 返回 shell。教程中的 `PS>`、`$`、`>>>` 一般是提示符，不能不加区别地一起复制。

### 1.4 参数、标准输入、标准输出

命令行参数随进程启动传入，例如 `--month 10`；标准输入是程序运行时可继续读取的输入流；标准输出和标准错误是两条输出通道。

程序打印内容到屏幕，不表示一定失败；程序没打印内容，也不表示一定成功。需要结合退出码和实际产物验证。

PowerShell 可通过 `$LASTEXITCODE` 检查刚执行的原生程序退出码。不要在失败之后继续运行依赖前一步结果的命令；安装脚本应该在关键步骤失败时停止。

## 第 2 章：四种位置与两类环境变量

### 2.1 位置不是只有一个

同一次运行可能出现四个不同位置：

| 位置 | 含义 | 观察方法 |
| --- | --- | --- |
| 当前工作目录 | 进程解析普通相对文件路径的基准 | Path.cwd() |
| 脚本文件位置 | 正在执行的源码位于哪里 | Path(__file__).resolve() |
| 解释器位置 | 哪个 Python 进程在执行 | sys.executable |
| 包安装位置 | 第三方包或本项目装在哪里 | 模块.__file__ 或 pip show |

例如你在 `D:\Work`，执行 `D:\Projects\demo\.venv\Scripts\python.exe D:\Projects\demo\main.py`。工作目录仍然是 `D:\Work`，不会因为脚本在 demo 中就自动切过去。

### 2.2 为什么 open("config.json") 经常出问题

代码：

```python
from pathlib import Path
text = Path("config.json").read_text(encoding="utf-8")
```

它读取工作目录下的文件，不是保证读取源码旁边的文件。编辑器可能把工作目录设为项目根目录，所以“编辑器运行正常”，而从别处调用就失败。

根据需求选择一种明确规则：

- 用户指定输入：通过命令行参数传路径，相对路径按工作目录解析。
- 脚本旁的固定演示文件：使用 `Path(__file__).resolve().parent / "文件名"`。
- 已安装包附带的小资源：使用 `importlib.resources`，见第二册。
- 用户配置、缓存、数据库：使用明确的数据目录，不要假定安装目录可写。

“把所有路径都改成绝对路径”也不是通用修复：写死自己的用户名，第二台照样失效。应明确路径的来源，而不是硬编码一台电脑的位置。

### 2.3 PATH 是程序搜索目录列表

写 `python` 时，shell 要找到相应命令；除了别名、函数等 shell 机制，还会查找 PATH 中的程序目录。激活环境后，虚拟环境的 Scripts 目录通常被放到更前面。

PATH 不是 Python 的包搜索路径，也不是“放任何东西进去都能运行”的万能列表。

PowerShell 观察：

```powershell
Get-Command python -All
$env:PATH -split ';'
```

Linux/macOS shell 的 PATH 一般用冒号分隔，可用 `command -v python3` 查看选中了哪个入口。不要直接把 Windows PATH 字符串复制到 Linux。

### 2.4 环境变量是进程得到的一组字符串

例如 `APP_MODE=development`，程序可用以下代码读取：

```python
import os
mode = os.environ.get("APP_MODE", "development")
```

PowerShell 设置当前会话的变量：

```powershell
$env:APP_MODE = 'development'
```

子进程通常继承启动它的父进程环境。当前终端改变量，不会神奇地修改已经运行的另一个终端或服务。

这与 Python 变量不同：Python 里的 `mode = "test"` 只是当前进程中的一个变量，不会自动变成全系统设置。

### 2.5 .env、环境变量、.venv 的关系

`.env` 通常是保存配置键值的文本文件。Python 并不会自动加载所有叫 .env 的文件，需要框架或代码明确读取。

`.venv` 是虚拟环境目录。激活 .venv 通常调整 PATH，但不保证替你加载应用的 .env 配置。

因此三个概念分别是“配置文件”“进程配置接口”“解释器和依赖的隔离环境”。

### 2.6 引号、空格与调用运算符

在 PowerShell 中，带空格的可执行文件完整路径需要这样调用：

```powershell
& 'D:\My Projects\demo\.venv\Scripts\python.exe' 'D:\My Projects\demo\main.py'
```

`&` 表示调用后面的命令；引号保证一个路径被作为一个参数处理。只写一个带引号的字符串，PowerShell 可能只是显示这个字符串。

Python 文件中构建路径优先用 pathlib。不要在跨平台代码里到处拼接反斜杠；反斜杠在 Python 普通字符串中还可能引出转义字符。

## 第 3 章：解释器、版本与虚拟环境

### 3.1 Python 语言与具体实现

Python 是语言；CPython 是最常见的解释器实现。还有其他实现，但不能假定为 CPython 提供的所有二进制包都能在其他实现使用。

一个环境的身份至少包括：解释器实现、版本、操作系统、CPU 架构、已安装包、相关系统动态库。只记“Python 3”远远不够。

Python 3.12 与 3.13 可能在语言和标准库行为上变化；带原生扩展的包还涉及二进制兼容性。3.12 的补丁版本通常更接近，但仍应记录实际验证版本。

### 3.2 为什么有多个 Python 并不稀奇

操作系统、编辑器、数据分析软件、应用捆绑运行时都可能带 Python。某个工具自带 Python 可供它自己使用，不代表适合作为你所有项目的统一基础环境。

项目先确定支持的 Python 版本，再选择对应解释器创建环境。不要先随便运行一个 `python`，失败后到处安装库。

查看身份的标准代码：

```python
import platform
import struct
import sys

print(sys.executable)
print(sys.version)
print(platform.python_implementation())
print(platform.system(), platform.machine())
print("指针位数:", struct.calcsize("P") * 8)
```

### 3.3 虚拟环境具体隔离什么

常规 venv 给项目提供自己的包安装位置和解释器入口。默认不直接使用系统 site-packages，但通常仍依赖基础 Python 的标准库及安装。

它隔离的重点是 Python 依赖，不是文件、网络和操作系统权限；不要用它执行不可信代码并以为安全。虚拟环境不是虚拟机，也不等于容器。[venv 官方说明](https://docs.python.org/3.12/library/venv.html)

两项观察值：

```python
import sys
print(sys.prefix)
print(sys.base_prefix)
```

在常规 venv 中，prefix 指向环境，base_prefix 指向基础安装。看到两者不同，是识别普通 venv 的实用方法；不要把它当成所有第三方环境管理器的完整判断规则。

### 3.4 创建、激活、使用、退出、重建

| 动作 | 是否安装依赖 | 是否启动业务程序 |
| --- | --- | --- |
| 创建环境 | 通常提供基本安装工具，不装你的业务依赖 | 否 |
| 激活 | 否 | 否 |
| pip install | 安装指定包及需要的依赖 | 通常不启动业务程序 |
| python main.py | 否 | 是 |
| deactivate | 不卸载 | 不会主动停止所有已启动进程 |

Windows：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip --version
```

macOS/Linux（前提是已安装对应解释器与 venv 支持）：

```sh
python3.12 -m venv .venv
./.venv/bin/python -m pip --version
```

明确指定路径可以不激活。若激活，Windows PowerShell 用 `.\.venv\Scripts\Activate.ps1`；bash/zsh 用 `source .venv/bin/activate`。不同 shell 的语法不能混用。

### 3.5 为什么要重建而不是搬运

环境中的启动脚本和配置可能记录绝对路径，原生库依赖平台，基础 Python 安装也可能不同。迁移项目目录后如果虚拟环境异常，重建通常比修补内部路径更可靠。

可靠迁移要保存“环境说明和创建步骤”。但在删除旧环境前，应确认新增依赖已记录，没有只存放在环境中的手工修改。第三方包内部不应成为项目唯一源码所在地。

## 第 4 章：pip 究竟安装了什么

### 4.1 下载仓库、安装工具和导入系统

这三者各有职责：

- 包索引提供可安装的发行包，PyPI 是常见的公共索引。
- pip 按要求解析依赖、获取发行物并安装到目标环境。
- Python import 在运行时寻找并加载模块。

`pip install` 与 `import` 不是同一个阶段。成功下载不代表安装成功；安装成功也不代表资源、驱动和配置齐全。

### 4.2 安装名不等于导入名

常见示例：安装 `Pillow`，代码导入 `PIL`；安装 `beautifulsoup4`，代码导入 `bs4`。命令行工具还可能没有明显的同名 import 入口。

所以看到 `import PIL` 报错，不应凭直觉寻找一个名叫 PIL 的新包；应查所属项目说明。

### 4.3 包安装到了哪里

一个已安装发行包可能包含：Python 源码、原生扩展、数据文件、命令行入口，以及 `.dist-info` 元数据目录。元数据记录版本和依赖等信息。

```powershell
.\.venv\Scripts\python.exe -m pip show Pillow
.\.venv\Scripts\python.exe -c "import PIL; print(PIL.__file__)"
```

第一条观察发行包信息，第二条观察实际导入来源。这里只是诊断例子，未安装该包时失败属于预期，不要求为学习安装所有示例库。

优先用 `目标Python -m pip`，确保安装动作属于你选择的解释器。[pip 使用说明](https://pip.pypa.io/en/stable/user_guide/)

### 4.4 wheel、源码包和原生扩展

wheel 是安装格式；源码包需要经过构建才能安装。纯 Python wheel 可以有较广适用范围，包含原生组件的 wheel 则常常限定 Python ABI、操作系统和架构。

看到示意文件名 `example-1.0-cp312-cp312-win_amd64.whl`，应想到 CPython 3.12、相应 ABI、Windows x64，而不是把它拿去 ARM Mac 安装。

当没有兼容 wheel，pip 可能尝试源码构建；构建就可能需要 C/C++ 编译器、头文件和系统库。“不需要编译器”是某一组依赖和平台的条件，不是所有 Python 项目的保证。

### 4.5 构建环境与运行环境

构建 wheel 所需的工具不一定是程序运行所需的工具。例如 setuptools 是某些项目的构建后端；pytest 是测试工具，不一定应随业务运行环境发布。

pip 构建源码项目时可能建立临时隔离的构建环境。`--no-build-isolation` 会改变这件事，使用前必须自己准备所需构建依赖。不要把它当作通用加速按钮。

`--no-deps` 则表示不解析安装项目依赖，与构建隔离是两个不同维度。

### 4.6 包安装为何会失败

四类问题分别处理：

1. **找不到兼容版本**：Python、平台、版本约束不匹配。
2. **网络失败**：索引无法访问、代理、证书、超时。
3. **构建失败**：没有 wheel，又缺编译条件或源码本身有问题。
4. **依赖冲突**：两个包对同一依赖提出无法同时满足的约束。

不要把四类问题都归结成“换镜像”。也不要为解决证书错误随手关闭验证或把密钥粘到公共日志里。

## 第 5 章：模块导入、入口与执行上下文

### 5.1 模块、普通包、命名空间包

通常一个 `.py` 文件是模块，包含 `__init__.py` 的目录可组织成普通包。模块也可能是原生扩展，不一定是可读 Python 文件。命名空间包可以没有普通的 `__init__.py`，用于更复杂的分发组织；初学项目先使用普通包。

安装发行包名、源码目录名、导入名、命令名可以各不相同。后面的示例安装名为 `textstats-kit`，导入名为 `textstats_kit`，命令名为 `textstats`。

### 5.2 import 不是复制粘贴

首次导入通常会执行模块顶层代码，并缓存模块对象。再次导入一般会复用缓存，而不是每次重新从头执行。[Python 导入系统](https://docs.python.org/3/reference/import.html)

因此不要在模块顶层无条件删除文件、连接真实数据库、弹窗口或启动服务器。应把这些操作放进明确调用的函数。

```python
def main():
    print("这里才开始执行应用逻辑")

if __name__ == "__main__":
    main()
```

文件作为入口运行时 `__name__` 通常是 `__main__`；作为模块导入时是模块名。这道判断让其他代码可以导入函数而不自动启动整个程序。

### 5.3 sys.path 与 PATH 完全不同

PATH 帮 shell 查找程序；sys.path 是 Python 模块搜索路径的一部分。运行方式、环境、安装信息等会影响它。

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(*sys.path, sep='\n')"
```

在常规启动方式中，直接运行脚本会把脚本所在目录放到搜索路径前部；用 `-m` 从模块启动则通常以工作目录参与搜索。`-I` 等隔离选项会改变默认行为。

不要把 `sys.path.append("我的绝对路径")` 当成每个导入问题的最终解法；它常常掩盖项目未正确安装、布局不合理或启动位置错误。

### 5.4 为什么文件不能随便命名

如果项目里有 `json.py`、`typing.py`、`requests.py`，可能遮住本来想导入的标准库或第三方模块。于是程序报出看似莫名其妙的“没有某属性”或循环导入错误。

先看 `module.__file__`，证明实际导入了谁。某些内建模块没有该属性，观察时用 `getattr(module, "__file__", None)` 更稳妥。

### 5.5 python 文件.py 与 python -m 包.模块

假设布局：

```text
src/
  sample_app/
    __init__.py
    cli.py
    helpers.py
```

cli.py 中写 `from .helpers import calculate`，点号表示相对于所属包。直接执行 cli.py 时可能缺少正确的包上下文；安装后用 `python -m sample_app.cli` 则按模块方式启动。

可编辑安装后，运行入口可以不依赖手动添加 src 到路径。`-m` 后写模块名，不写 `.py` 后缀，也不用文件系统斜杠。

### 5.6 循环导入是结构问题

若 a 导入 b，b 又在顶层导入 a 中尚未定义的对象，就可能看到 partially initialized module。把公共逻辑提取到第三个模块，或降低模块间依赖，往往比任意调换 import 顺序更合理。

### 5.7 为什么修改后仍像旧代码

检查以下几种不同可能：

- 当前进程没有重启，使用的是已加载对象。
- 导入的是另一个目录中的同名包。
- 当前环境普通安装了一份旧代码，没有可编辑安装。
- 点的是旧 exe，而不是源码入口。
- Notebook 内核仍保存旧状态。

不要第一反应删除所有 `__pycache__`。缓存存在本身是正常现象，先证明运行入口和代码来源。

## 第 6 章：编辑器、调试器和 Notebook 为什么会“另用一个环境”

编辑器可以有终端解释器选择、运行按钮配置、调试配置、测试发现配置。它们可能不是同一份设置。打开了某项目文件夹，不代表每个按钮自动选择了正确环境。

在怀疑环境不一致时，让实际运行的代码打印 sys.executable、Path.cwd()、目标模块.__file__。比只看界面左下角显示的名称更有证据。

Notebook 的代码由内核进程执行。启动 Jupyter 的环境、浏览器页面和实际内核可能是不同层；终端安装了包，内核未必能看到。

Notebook 诊断先执行：

```python
import sys
print(sys.executable)
```

更换解释器后选择正确内核，必要时重启内核。Notebook 单元格可以乱序执行，变量残留会制造“我的电脑上能跑”的假象；交付前从干净内核按顺序运行全部单元格。

本课程实验采用脚本和终端，避免一开始同时引入内核管理；理解这层关系后再学习数据分析工具会更容易。

## 第一册检查题

1. 同一个脚本从两个目录启动，代码没变，为什么可能读取不同文件？
2. Python 包装在环境 A，程序用环境 B，激活 A 之后已经运行的 B 进程会自动改变吗？
3. `python -m pip` 中的 `-m` 与 `python -m sample_app.cli` 是否表达同一种启动方式？
4. 为何不把大型网络请求写在模块顶层？
5. 为什么 `pip install Pillow` 与 `import PIL` 不矛盾？
6. 为什么“我用了虚拟环境”不能证明不可信代码是安全的？

答案与实验见[第三册](03-labs-and-troubleshooting.md)。下一步学习文件结构和依赖配方，而不是继续记更多安装命令。

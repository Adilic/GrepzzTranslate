# 第一册：计算机怎样找到并运行 Python

[课程目录](README.md) · [下一册](02-projects-and-reproducibility.md)

## 第 1 章：一次程序运行到底发生了什么

### 1.1 保存了代码，不等于程序正在运行

磁盘上的 `hello.py` 是保存代码的文件。要运行它，还需要 Python 解释器——也就是执行 Python 代码的程序。启动后，电脑中这一次正在运行的程序叫“进程”；运行结束，进程退出，文件还在。

同一个文件可以同时运行多次，各有自己的进程。修改文件后，已经启动的程序可能还在用之前读入的代码。因此，改完长期运行的程序，通常需要重启才能看到效果。

关窗口不一定结束进程；没有窗口，也不代表程序没运行。

### 1.2 从键盘输入到结果输出

下面只用来拆解命令，不必执行。假设已有 report.py，在 PowerShell 输入：

```powershell
python report.py --month 10
```

可以分成六步理解：

1. 终端窗口收到你输入的文字，交给 PowerShell 处理。
2. PowerShell 找到 `python` 对应的程序，并把后面的内容作为参数交给它。
3. 找到解释器后，操作系统启动一个进程。
4. Python 根据参数找到 report.py，读取并执行它。
5. 程序加载需要的代码、读取文件，输出结果。需要用到的其他代码或软件，叫“依赖”。
6. 运行结束后，程序返回一个数字，叫“退出码”。通常 0 表示成功，其他数字表示失败；具体含义看程序说明。

| 错误发生处 | 可能的提示 | 应关注什么 |
| --- | --- | --- |
| 找不到命令 | python 无法识别 | shell、PATH、解释器安装 |
| 找不到脚本 | can't open file | 工作目录、脚本路径 |
| 导入失败 | ModuleNotFoundError | 当前环境、导入路径、包名 |
| 读取资源失败 | FileNotFoundError | 程序访问了哪个文件 |
| 业务失败 | 输入不是合法月份 | 程序逻辑和输入数据 |

### 1.3 终端、shell、Python 交互模式

- 终端是显示输入输出的界面，例如 Windows Terminal。
- shell 是接收和执行命令的程序。Windows 中常用 PowerShell，其他系统也常用 bash。
- Python 交互模式是 Python 启动后的输入环境，通常提示符是 `>>>`。

看到 `PS ...>`，输入 PowerShell 命令；看到 `>>>`，输入 Python 代码。把 pip 安装命令贴进 `>>>`，通常会报 SyntaxError。

在 Python 交互模式输入 `exit()` 返回 shell。教程中的 `PS>`、`$`、`>>>` 一般是提示符，不能不加区别地一起复制。

### 1.4 参数、标准输入、标准输出

命令行参数是启动时交给程序的信息，例如 `--month 10` 表示指定月份。标准输入让程序运行中继续接收内容；标准输出通常放结果，标准错误通常放报错。后两者常显示在同一个窗口，但可以分别保存。

程序打印内容到屏幕，不表示一定失败；程序没打印内容，也不表示一定成功。需要结合退出码和实际产物验证。

在 PowerShell 中，执行程序后输入 `$LASTEXITCODE`，可查看它的退出码。若安装或生成文件失败，先处理错误，再执行需要这些结果的下一步。

## 第 2 章：程序在哪里找文件，在哪里找设置

### 2.1 位置不是只有一个

同一次运行可能出现四个不同位置：

| 位置 | 含义 | 观察方法 |
| --- | --- | --- |
| 当前工作目录 | 程序当前以哪个文件夹为起点找文件 | Path.cwd() |
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

这里的 `config.json` 没有写完整路径，叫“相对路径”。程序会去当前工作目录找它。编辑器可能刚好把工作目录设在项目中；换个地方启动，程序就可能找不到它。

根据需求选择一种明确规则：

- 用户指定输入：通过命令行参数传路径，相对路径按工作目录解析。
- 脚本旁的固定演示文件：使用 `Path(__file__).resolve().parent / "文件名"`。
- 已安装包附带的小资源：使用 `importlib.resources`，见第二册。
- 用户配置、缓存、数据库：使用明确的数据目录，不要假定安装目录可写。

别把自己的用户名和路径写死在代码中，否则换电脑仍会失败。

### 2.3 PATH 是程序搜索目录列表

输入 `python` 时，PowerShell 要先找到它。PATH 保存了一串用于查找程序的文件夹。激活虚拟环境通常把该环境的 Scripts 文件夹排到前面，让其中的 Python 优先被找到；别名等设置也可能影响结果。

PowerShell 观察：

```powershell
Get-Command python -All
$env:PATH -split ';'
```

Linux/macOS 用 `command -v python3` 查看命令位置；PATH 用冒号分隔，不能直接复制 Windows 的值。

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

在这个终端里设置后，再从这里启动的程序通常能读到这个值。已经打开的另一个终端或程序，不会因此自动更新。

这与 Python 变量不同：Python 里的 `mode = "test"` 只是当前进程中的一个变量，不会自动变成全系统设置。

### 2.5 .env、环境变量、.venv 的关系

`.env` 通常是保存配置键值的文本文件。Python 并不会自动加载所有叫 .env 的文件，需要框架或代码明确读取。

`.venv` 是虚拟环境目录。激活 .venv 通常调整 PATH，但不保证替你加载应用的 .env 配置。

记法：`.env` 是存设置的文件；环境变量是程序能读取的设置；`.venv` 是放项目 Python 环境的文件夹。名字相像，用途不同。

### 2.6 引号、空格与调用运算符

在 PowerShell 中，带空格的可执行文件完整路径需要这样调用：

```powershell
& 'D:\My Projects\demo\.venv\Scripts\python.exe' 'D:\My Projects\demo\main.py'
```

`&` 表示调用后面的命令；引号保证一个路径被作为一个参数处理。只写一个带引号的字符串，PowerShell 可能只是显示这个字符串。

Python 代码中优先用 pathlib 拼路径，减少手写斜杠和转义造成的错误。

## 第 3 章：解释器、版本与虚拟环境

### 3.1 Python 语言与具体实现

Python 是语言的名字；CPython 是执行这种语言的一种程序，也是最常见的一种。其他实现也能运行 Python，但为 CPython 制作的某些包不一定适用。

描述环境时，要说清：使用哪一种 Python、哪个版本、什么系统、什么 CPU 类型，以及安装了哪些包和系统库。只说“Python 3”，还不足以让另一台电脑照着准备。

3.12 和 3.13 可能支持不同功能，也可能需要不同版本的包。3.12.1、3.12.2 这样的补丁版本通常差异较小，但仍要记录自己实际用过的版本。

### 3.2 为什么有多个 Python 并不稀奇

系统和各种软件可能各带一份 Python。它们用于各自的工作，不一定适合你的项目。

先看项目支持哪个版本，再选 Python 创建环境。

下面的 Python 代码可显示路径、版本、实现、系统和位数：

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

venv 是 Python 自带的虚拟环境工具。它为项目准备一个环境文件夹，通常叫 `.venv`。这个项目安装的包放在自己的 `site-packages` 文件夹里，默认不混用系统 Python 安装的第三方包。它仍会使用基础 Python 的标准库。

它主要让不同项目各装各的依赖，例如 A 用旧版包、B 用新版包。它不限制程序读文件或访问网络，也不提供另一套操作系统，因此不是虚拟机或安全沙箱。[venv 官方说明](https://docs.python.org/3.12/library/venv.html)

两项观察值：

```python
import sys
print(sys.prefix)
print(sys.base_prefix)
```

使用 venv 时，`prefix` 通常指向 `.venv`，`base_prefix` 指向创建它的基础 Python。两条路径不同，说明当前使用的是这类虚拟环境；其他环境工具可能有不同规则。

### 3.4 创建、激活、使用、退出、重建

| 动作 | 是否安装依赖 | 是否启动业务程序 |
| --- | --- | --- |
| 创建环境 | 通常提供基本安装工具，不装你的业务依赖 | 否 |
| 激活 | 否 | 否 |
| pip install | 安装指定包及需要的依赖 | 通常不启动业务程序 |
| python main.py | 否 | 是 |
| deactivate | 不卸载 | 不会主动停止所有已启动进程 |

Windows：在准备存放项目的文件夹中打开 PowerShell，逐条执行。第一条创建 `.venv`；第二条显示其中 pip 的版本和位置。前提是 `py -3.12` 可用。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip --version
```

macOS/Linux（前提是已安装对应解释器与 venv 支持）：

```sh
python3.12 -m venv .venv
./.venv/bin/python -m pip --version
```

上面的命令直接指定 `.venv` 中的 Python，所以不需要先激活。激活只是让当前终端输入简短的 `python` 时，更方便地选到它。PowerShell 的激活命令是 `.\.venv\Scripts\Activate.ps1`，bash/zsh 则用 `source .venv/bin/activate`。

### 3.5 为什么要重建而不是搬运

`.venv` 里可能记录了第一台电脑的路径，其中一些文件也只适合原来的系统。换电脑时，带走源码和依赖清单，在新电脑重新创建 `.venv`，比复制旧环境更可靠。

删除旧环境前，先确认新增依赖都已记下来。自己的代码应保存在项目源码中；如果只修改了 `.venv` 里的第三方包，重建后那些修改就会丢失。

## 第 4 章：pip 究竟安装了什么

### 4.1 去哪里下载、谁来安装、谁来使用

这三者各有职责：

- PyPI 等包索引：提供包的名称、版本和下载信息，可以理解为查找 Python 包的目录。
- pip：选出符合要求的包版本，下载并安装到指定环境。
- import：程序运行时，找到并加载要使用的模块。

`pip install` 与 `import` 不是同一个阶段。成功下载不代表安装成功；安装成功也不代表资源、驱动和配置齐全。

### 4.2 安装名不等于导入名

常见示例：安装 `Pillow`，代码导入 `PIL`；安装 `beautifulsoup4`，代码导入 `bs4`。命令行工具还可能没有明显的同名 import 入口。

### 4.3 包安装到了哪里

安装一个包，可能同时装入 Python 代码、其他语言写的组件、数据文件和命令入口。`.dist-info` 文件夹保存它的名称、版本、依赖等说明；这些说明统称“元数据”。

```powershell
.\.venv\Scripts\python.exe -m pip show Pillow
.\.venv\Scripts\python.exe -c "import PIL; print(PIL.__file__)"
```

第一条看安装信息，第二条看实际加载的文件。未安装 Pillow 时会失败；这是诊断示例，不必特意安装。

优先用 `目标Python -m pip`，确保安装动作属于你选择的解释器。[pip 使用说明](https://pip.pypa.io/en/stable/user_guide/)

### 4.4 wheel、源码包和原生扩展

wheel 是以 `.whl` 结尾的 Python 安装包。源码包则需要先“构建”，也就是把源码整理、必要时编译成可安装的文件。只含 Python 代码的 wheel 通常适用范围更广；含 C/C++ 等组件的包，常对 Python 版本、系统和 CPU 类型有要求。

例如 `example-1.0-cp312-cp312-win_amd64.whl`，适用于 CPython 3.12、Windows x64，不能直接拿到 ARM Mac 使用。其中 ABI 标签表示它与解释器底层接口的兼容要求，初学时不必背这些缩写。

找不到兼容的 wheel 时，pip 可能尝试从源码构建。如果还需要编译 C/C++，电脑就得准备编译器和相关文件。这是有些包装起来很顺利、有些却报编译错误的原因。

### 4.5 构建环境与运行环境

制作安装包和运行程序，需要的工具可能不同。例如 setuptools 用于制作某些项目的安装包，pytest 用于测试；用户只运行程序时不一定需要它们。

pip 构建源码时，可能临时建一个环境，专门安装构建工具。`--no-build-isolation` 会关闭这一步，改由你提前准备工具；不了解原因时不要随便加这个选项。

`--no-deps` 是另一个意思：不替项目安装它所依赖的包。它不负责开关上面的临时构建环境。

### 4.6 包安装为何会失败

四类问题分别处理：

1. **找不到兼容版本**：Python、平台、版本约束不匹配。
2. **网络失败**：索引无法访问、代理、证书、超时。
3. **构建失败**：没有 wheel，又缺编译条件或源码本身有问题。
4. **依赖冲突**：两个包对同一依赖提出无法同时满足的约束。

先区分原因，再处理；换下载源解决不了所有问题。证书错误也不应靠关闭校验来绕过。

## 第 5 章：import 怎样找到代码，程序从哪里开始

### 5.1 一个文件和一个包有什么关系

通常，一个 `.py` 文件就是一个“模块”。把相关模块放进带 `__init__.py` 的文件夹，可以组成普通“包”。也有其他形式：模块可能由 C/C++ 编写，命名空间包可以没有 `__init__.py`。本课程先用最常见的普通包。

安装发行包名、源码目录名、导入名、命令名可以各不相同。后面的示例安装名为 `textstats-kit`，导入名为 `textstats_kit`，命令名为 `textstats`。

### 5.2 import 不是复制粘贴

第一次 import 某个模块，通常会执行其中不在函数内的代码，这些叫“顶层代码”。Python 会记住已加载的模块；同一个进程再次 import 时，一般直接复用。[Python 导入系统](https://docs.python.org/3/reference/import.html)

因此不要在模块顶层无条件删除文件、连接真实数据库、弹窗口或启动服务器。应把这些操作放进明确调用的函数。

```python
def main():
    print("这里才开始执行应用逻辑")

if __name__ == "__main__":
    main()
```

直接运行这个文件时，判断成立，会调用 `main()`；其他文件 import 它时，判断不成立，不会自动调用 `main()`。这样，别人能使用其中的函数，又不会一导入就启动整个应用。

### 5.3 sys.path 与 PATH 完全不同

PATH 用来找 `python.exe` 这样的程序；`sys.path` 用来帮 Python 找要 import 的模块。两者找的东西不同。下面在已有 `.venv` 的项目目录执行，可查看模块搜索目录：

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(*sys.path, sep='\n')"
```

通常，直接运行脚本会搜索脚本目录，`-m` 启动会搜索工作目录；`-I` 等选项会改变这一行为。

不要靠把本机绝对路径塞进 sys.path 来修复所有导入问题；先查安装和启动方式。

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

假设 cli.py 写着 `from .helpers import calculate`。点号的意思是“到我所属的包里找 helpers”。直接运行 cli.py 时，Python 可能不知道它属于哪个包；安装项目后用 `python -m sample_app.cli`，就明确了这个关系。

可编辑安装后，运行入口可以不依赖手动添加 src 到路径。`-m` 后写模块名，不写 `.py` 后缀，也不用文件系统斜杠。

### 5.6 循环导入是结构问题

a 需要 b，b 又马上向 a 要一个还没定义好的函数，就可能报 `partially initialized module`，意思是“模块还没加载完”。可以把双方共用的函数放进第三个模块，让 a 和 b 都去那里取。

### 5.7 为什么修改后仍像旧代码

- 当前进程没有重启，使用的是已加载对象。
- 导入的是另一个目录中的同名包。
- 当前环境普通安装了一份旧代码，没有可编辑安装。
- 点的是旧 exe，而不是源码入口。
- Notebook 内核仍保存旧状态。

先查运行的是哪份代码，不要一报错就删除 `__pycache__`；有缓存是正常的。

## 第 6 章：编辑器、调试器和 Notebook 为什么会“另用一个环境”

编辑器中的终端、运行按钮、调试按钮和测试按钮，可能各自选了不同的 Python。打开同一个项目文件夹，不代表这些按钮一定使用同一个环境。

在怀疑环境不一致时，让实际运行的代码打印 sys.executable、Path.cwd()、目标模块.__file__。比只看界面左下角显示的名称更有证据。

Notebook 页面负责显示，真正执行代码的是后台的“内核”进程。它可能使用另一套 Python，所以你在终端装好的包，Notebook 不一定能找到。

Notebook 诊断先执行：

```python
import sys
print(sys.executable)
```

换环境后，要让 Notebook 选择对应内核，必要时重启。单元格若乱序执行，还可能用到之前留下的变量。交给别人前，应重启内核，再从上到下执行一遍。

## 第一册检查题

1. 同一个脚本从两个目录启动，代码没变，为什么可能读取不同文件？
2. Python 包装在环境 A，程序用环境 B，激活 A 之后已经运行的 B 进程会自动改变吗？
3. `python -m pip` 中的 `-m` 与 `python -m sample_app.cli` 是否表达同一种启动方式？
4. 为何不把大型网络请求写在模块顶层？
5. 为什么 `pip install Pillow` 与 `import PIL` 不矛盾？
6. 为什么“我用了虚拟环境”不能证明不可信代码是安全的？

答案与实验见[第三册](03-labs-and-troubleshooting.md)。下一步学习文件结构和依赖配方，而不是继续记更多安装命令。

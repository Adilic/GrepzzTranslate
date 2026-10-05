# 第三册：动手实验、故障案例与参考答案

[课程目录](README.md) · [第一册](01-runtime-and-environments.md) · [第二册](02-projects-and-reproducibility.md)

这一册用六个实验练习前面的内容。一次只做一步：确认所在目录，读懂预期结果，再执行命令。结果不对就停下来排查。

## 开始前：实验约定

实验使用 Windows PowerShell 和 Python 3.12。PowerShell 代码块输入终端，Python 代码块按说明保存到文件；不要把两种代码混着粘贴。`py -3.12` 需要已经能启动 Python 3.12。

新建学习目录，例如 D:\PythonLearning；没有 D 盘就选别处。示例路径按自己的电脑替换。

准备一份学习记录，逐次填：

| 项目 | 记录什么 |
| --- | --- |
| 目标 | 这次想验证哪个概念 |
| 工作目录 | Get-Location 的结果 |
| 解释器 | sys.executable 的结果 |
| 预测 | 运行前认为会发生什么 |
| 实际 | 输出、退出码或文件变化 |
| 结论 | 哪个假设得到证明或被推翻 |

除故意报错的实验外，出错先停下。开启文件扩展名显示，避免把 hello.py 保存成 hello.py.txt。

### 先认识实验中的少量语法

```python
name = "Python"
print(name)
```

第一行用 name 这个名字保存文字 Python；第二行把它显示出来。引号内是文字，name 则是存放这段文字的变量名。

```python
def greet(name):
    return "Hello " + name
```

`def` 定义一段可重复使用的操作，叫函数；缩进的行属于这个函数。`return` 交回结果。只有调用 `greet("Python")` 时，才会得到 Hello Python；单写定义不会执行它。

```python
from pathlib import Path
```

这句让我们能使用 pathlib 里的 Path 来处理路径。pathlib 是 Python 自带的标准库，不需要另外安装。

## 实验 1：证明文件位置不等于工作目录

### 目标

观察同一个脚本，从不同目录启动时，哪些值会变、哪些值不变。

### 操作

在一个新的 `path-lab` 文件夹里创建 `where_am_i.py`：

```python
from pathlib import Path
import sys

print("解释器:", sys.executable)
print("工作目录:", Path.cwd())
print("脚本位置:", Path(__file__).resolve())
print("相对文件解析到:", Path("input.txt").resolve())
```

在 path-lab 文件夹里运行：

```powershell
py -3.12 where_am_i.py
```

再到上一级运行：

```powershell
cd ..
py -3.12 .\path-lab\where_am_i.py
```

### 先预测，再比较

脚本位置应当保持一致；工作目录会改变；`input.txt` 的解析位置跟着工作目录改变。程序不要求这个输入文件真的存在，因为这里只是计算路径。

### 这能解释什么问题

“我的脚本明明和配置文件放在一起，为什么找不到？”可能是代码使用了工作目录相对路径。

如果配置设计为脚本旁边的固定文件：

```python
config_path = Path(__file__).resolve().parent / "config.json"
```

若由用户选择配置，则读取用户传入的路径；不要一律强制切换工作目录。

### 达标问题

你能否用一句话解释 Path.cwd() 与 `__file__` 的区别？不要只回答“一个短一个长”。

## 实验 2：观察虚拟环境身份与激活

### 目标

确认自己正在用哪个 Python，并试一试：不激活，能不能使用虚拟环境。

### 操作

回到你选定的 path-lab：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)"
.\.venv\Scripts\python.exe -m pip --version
```

第二条打印三条路径：依次是环境中的 python.exe、环境文件夹、基础 Python 文件夹；后两条应不同。第三条显示 pip 信息，其路径应在这个 `.venv` 内。

再运行：

```powershell
.\.venv\Scripts\python.exe where_am_i.py
```

这里直接指定了 `.venv` 里的 python.exe，所以即使没激活也能运行。激活只是省去每次输入这段路径。

如果当前 PowerShell 允许执行激活脚本，可继续：

```powershell
.\.venv\Scripts\Activate.ps1
python -c "import sys; print(sys.executable)"
Get-Command python
deactivate
```

如果策略阻止激活，跳过这一步，不需要为基础实验修改全局策略。继续使用明确路径即可。

### 两个常见误解

1. “终端前面有 .venv，就永远不会用错 Python。”错误。程序可能通过别的明确路径启动；编辑器也可能使用其他配置。最终看实际进程的 sys.executable。
2. “deactivate 会删除依赖。”错误。它主要撤销当前 shell 的激活状态，文件仍在磁盘。

### 达标问题

关闭这个终端，开一个新终端。是否还需要重新安装依赖？是否还可以用完整解释器路径运行？

## 实验 3：从小脚本走向可安装的包

### 目标

理解普通函数、包结构、可编辑安装与运行入口。

### 准备

把 [textstats-kit 示例](examples/textstats-kit/README.md) 复制到学习目录，如 D:\PythonLearning\textstats-kit。只复制源码，不搬旧 .venv，也不要覆盖已有练习。

进入复制后的示例根目录，应该能看到 pyproject.toml、README.md、src、tests。

```powershell
Get-Location
Get-ChildItem
py -3.12 -m venv .venv
```

### 先故意做一个会失败的动作

在未安装本项目的新环境中运行：

```powershell
.\.venv\Scripts\python.exe -m textstats_kit --demo
```

正常的新环境会提示 `No module named textstats_kit`。文件虽然已复制到 src，环境却还不知道去那里找。我们故意先观察这个错误，下一步安装后再比较。

如果意外成功，先查 `sys.executable` 和模块的 `__file__`：可能用到了另一个环境，或以前装过的同名包。再检查 sys.path 和环境变量。

### 安装后再运行

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m textstats_kit --demo
.\.venv\Scripts\textstats.exe --demo
.\.venv\Scripts\python.exe -c "import textstats_kit; print(textstats_kit.__file__)"
```

初次安装开发和构建工具通常需要联网；示例运行时只用标准库。

`-e` 表示使用可编辑源码，`.` 表示当前文件夹，`[dev]` 表示同时安装配置中那组开发工具。它们都装到当前 `.venv`，没有另建一个叫 dev 的环境。

第二、三条命令应得到下面相同结果：characters 为 21，lines 为 2，words 为 3。第四条打印的文件路径应在你的学习副本 src 中。

```json
{"characters": 21, "lines": 2, "words": 3}
```

### 逐文件阅读

先看 core.py：

```python
def summarize(text: str) -> dict[str, int]:
    return {
        "characters": len(text),
        "lines": len(text.splitlines()),
        "words": len(text.split()),
    }
```

`text: str` 提示输入应是文字；`dict[str, int]` 提示返回的是“名称对应整数”的结果。这些类型标注方便阅读和检查，不会自动修正传错的输入。

`len(text)` 数字符串里的 Unicode 码点，换行也算；码点不总等于肉眼看到的字数。`splitlines()` 拆成行，`split()` 按空格、换行等空白拆分。所以 words 不是中文或日文的真实词数；21 是按文本读取时统一换行后的结果。

再看 cli.py：argparse 负责读懂 --demo 等参数，pathlib 负责读用户指定的文件，importlib.resources 负责读包内示例。最后，它调用刚才的函数，把结果按 JSON 格式显示出来。

### 不启动命令界面，也能调用计算函数

```powershell
.\.venv\Scripts\python.exe -c "from textstats_kit import summarize; print(summarize('one two'))"
```

这只调用计算函数，不解析命令参数。同一个函数以后也能给图形界面或网站使用。

### 修改练习

先改学习副本 README 中的一句话，再运行 --demo，结果不会变，因为说明文字不是程序代码。再改 cli.py 中的帮助文字，执行 `.\.venv\Scripts\python.exe -m textstats_kit --help`，应看到新文字。

## 实验 4：用测试明确输入输出的边界

### 目标

知道“运行过一次”与“验证了关键行为”的区别。

### 操作

仍在示例根目录：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

未修改的示例应显示 `6 passed`，表示 6 项测试通过。它们检查空文本、换行、中文等字符、外部文件、换目录读取包内文件，以及缺文件时是否正确报错。

### 为什么这几个测试有用

这些测试各查一个容易漏掉的问题：空文本怎么算？结尾换行是否多算一行？中文路径能不能读？换目录还找得到示例吗？缺文件会不会误报成功？

### 给自己加一道测试

在学习副本 tests/test_core.py 中添加：

```python
def test_blank_line_is_counted():
    assert summarize("a\n\nb") == {
        "characters": 4,
        "lines": 3,
        "words": 2,
    }
```

先手算：a、两个换行、b，共 4 个码点；中间的空行算一行，共 3 行；按空白拆开只剩 a、b，共 2 个词。添加测试后再运行全部测试，应显示 `7 passed`。

### 学会读失败

在自己的学习副本中暂时把这个预期 lines 改成 2，再运行单个测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_core.py::test_blank_line_is_counted -q
```

应看到实际值与预期值不符。看懂后把 2 改回 3，再测试。

## 实验 5：制作 wheel，并在第二个环境验证

### 目标

确认交给别人的安装包能独立工作，没有偷偷使用开发目录中的文件。

### 构建

仍在示例根目录，用开发环境执行：

```powershell
.\.venv\Scripts\python.exe -m build --wheel
```

构建过程可能建立临时构建环境并获取构建依赖。输出包含：

```text
dist/textstats_kit-0.1.0-py3-none-any.whl
```

文件名中的 textstats_kit 用下划线，配置中的 textstats-kit 用短横线，这是打包时正常的名字转换，不需要改名。

### 第二环境普通安装

```powershell
py -3.12 -m venv .verify-venv
.\.verify-venv\Scripts\python.exe -m pip install --no-deps .\dist\textstats_kit-0.1.0-py3-none-any.whl
.\.verify-venv\Scripts\python.exe -c "import textstats_kit; print(textstats_kit.__file__)"
```

这次不用 `-e`，因为要检查打包出来的文件。`--no-deps` 表示跳过依赖安装；本示例运行时只用标准库，才可以这样做。其他项目不能直接照用。

导入路径现在应位于 .verify-venv 的 site-packages，而不是 src。

### 从项目外运行

先保存解释器路径，再暂时切到系统临时目录：

```powershell
$lessonPython = (Resolve-Path .\.verify-venv\Scripts\python.exe).Path
Push-Location $env:TEMP
try {
    & $lessonPython -I -m textstats_kit --demo
} finally {
    Pop-Location
}
```

`$lessonPython` 记住完整的 Python 路径；`Push-Location` 临时换目录；`finally` 中的 `Pop-Location` 负责回到原目录。`-I` 减少当前目录和用户环境对导入的影响，但不限制程序读文件或联网。

仍应看到 characters=21、lines=2、words=3。这说明安装包里的代码和 example.txt 都能使用，即使当前不在源码文件夹。

### 比较两种安装

| 观察 | .venv 可编辑安装 | .verify-venv 普通 wheel 安装 |
| --- | --- | --- |
| 导入来源 | 开发 src | 环境 site-packages |
| 修改工作区函数后重启 | 通常马上使用新函数 | 仍使用已安装版本 |
| 目的 | 开发迭代 | 验证交付产物 |

如果开发环境能运行、验证环境不能，先查安装包是否漏文件、漏依赖，以及路径和 Python 是否正确。不要把开发目录加进去救急，否则就无法证明安装包能独立运行。

## 实验 6：模拟第二台电脑，写出迁移清单

### 目标

写清换电脑要带走什么、重新安装什么，以及怎样确认迁移成功。

### 不必马上拿第二台电脑

先在纸上为教学项目写清：

- 源码位置／提交号。
- 需要的 Python 版本与平台假设。
- 运行依赖：本示例无第三方业务依赖。
- 开发依赖：测试与构建工具。
- 安装方式：可编辑源码或 wheel。
- 配置：输入路径由命令行提供。
- 包内资源：example.txt 随 wheel 分发。
- 验收：从其他目录执行 --demo；读取自己构造的 UTF-8 文件。

更复杂的项目，还要把数据库、模型、浏览器驱动或 GPU 条件加入清单。

### 真正到第二台电脑时

要继续开发：拿源码，创建新 `.venv`，安装依赖和项目，再运行测试。只想安装这个 Python 包：拿 wheel，用兼容的 Python 安装，再试一次实际功能。

### 挑战题

如果希望依赖版本完全记录，你会用什么清单？如果希望离线安装，还缺哪些文件？如果目标是另一种操作系统，还应检查哪些假设？参考答案见后文。

## 故障案例：用证据而不是猜测排错

### 案例 A：安装成功，运行却找不到包

**现象**：执行 `pip install some-package` 成功，运行脚本仍报 ModuleNotFoundError。

**常见原因**：pip 属于系统 Python，脚本属于项目 .venv；也可能安装名与导入名不同。

**收集证据**：

```powershell
Get-Command python -All
Get-Command pip -All
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip show some-package
```

这里 some-package 是占位名字，必须换成真正需要检查的发行包。用目标解释器安装正确依赖，再运行同一解释器；不要向所有 Python 环境重复乱装。

### 案例 B：编辑器正常，计划任务失败

**现象**：手工运行能读配置，计划任务报找不到文件。

**候选原因**：工作目录、执行账号、环境变量、权限或解释器不同。

**排查**：在受控日志中记录 sys.executable、Path.cwd() 和具体目标文件路径；检查任务的运行账号与启动目录。避免直接输出所有环境变量，因为可能含秘密。

**修复原则**：明确解释器、路径来源和必要配置。不要仅凭手工成功就认定计划任务环境一致。

### 案例 C：import json 后缺少标准函数

**现象**：标准库看似缺少 loads，或者出现循环导入提示。

**候选原因**：自己的文件叫 json.py，遮住标准库。

**证据**：

```python
import json
print(getattr(json, "__file__", None))
```

若指向你的工作区，换一个不冲突的文件名并重启进程。不要先升级 Python 或随便安装名叫 json 的第三方包。

### 案例 D：attempted relative import with no known parent package

**现象**：直接执行包内部 cli.py，而它使用 `from .core import ...`。

**原因**：直接运行 cli.py 时，Python 不知道点号指的是哪个包。

**修复**：先安装项目，然后使用 `python -m 包名.模块名` 或声明的命令入口。不要为了消除错误随意删除相对导入中的点并追加多个路径。

### 案例 E：No matching distribution found

**可能原因**：版本拼写错误、当前 Python 太新／太旧、目标架构不支持、指定包源缺包，或仅允许 wheel 时没有对应产物。

**观察**：Python 版本、platform.machine()、pip 输出所访问的源、上游支持说明。网络超时与确实没有兼容版本不是同一件事。

**修复原则**：选择项目支持的解释器和版本组合。不要把“不支持的平台”通过不断重试变成“网络问题”。

### 案例 F：开发目录运行正常，wheel 安装后找不到 example.txt

**原因**：源码存在资源，但构建配置没有包含它，或者运行时用工作目录读取它。

**验证**：检查 wheel 内文件列表；从安装后的包使用 importlib.resources 读取。

**修复**：把资源写入构建配置，重新打包、安装，再换到项目外运行。不要靠额外复制源码来补洞。

### 案例 G：两台 requirements 一样，仍然一台失败

**可能不同**：Python 实现与版本、架构、OS、系统动态库、驱动、环境变量、资源版本、文件大小写、输入编码。

**处理**：按层比较环境清单，而不是只比较 pip list。一份依赖清单不可能代替数据库内容和操作系统能力。

### 案例 H：修改源码，执行仍是旧行为

**依次检查**：

1. 运行的是源码、普通安装包还是旧 exe？
2. 实际模块 __file__ 指向哪里？
3. 进程／Notebook 内核是否已重启？
4. 是否改了另一份同名克隆目录？
5. 若改的是入口元数据，是否重新安装？

这些都确认后，再查缓存和打包问题。

### 案例 I：Git 已提交，另一台仍看不到

**区别**：保存只是改了文件；add 选出要提交的修改；commit 留下本机版本；push 才上传到远端。另一台还要在正确分支 pull，才能更新文件；fetch 只获取远端信息，不直接更新工作文件。

先看两台提交号和分支，再看远端。不要直接复制整个 .git 文件夹去覆盖另一个仓库。

### 案例 J：激活虚拟环境后仍无法安装系统组件

**原因**：虚拟环境管理的是 Python 环境，不是系统管理员权限，也不是操作系统包管理器。

## 检查题参考答案

### 第一册

1. 相对路径从工作目录开始找。脚本没变，启动目录变了，找到的文件就可能不同。
2. 不会。B 已经在运行；在另一个终端激活 A，不能把 B 正在使用的 Python 换掉。
3. 是，都是让选定解释器按模块方式执行，只是模块分别是 pip 和业务模块。
4. 测试或其他程序也可能 import 这个模块。如果顶层直接发网络请求，一导入就会请求，可能卡住或失败。放进函数，等明确调用时再做。
5. 安装时的包名和代码中 import 的名字可以不同，由提供这个包的项目决定。
6. venv 不限制程序访问文件和网络，程序仍拥有当前账号允许的能力。

### 第二册

1. 源码目录可能有构建未包含的资源，开发环境也可能装有未声明依赖。普通安装后的行为要独立验证。
2. 应用希望固定自己部署的环境；库要与使用者其他依赖共存，通常表达兼容范围。同时仍可在库自己的测试中固定或覆盖多个版本组合。
3. requirements 说“需要安装它”；constraints 说“如果需要安装它，版本要遵守这个限制”。
4. Python、平台、系统组件、驱动、配置、资源、数据和外部服务都可能不同。
5. pull 更新 Git 管理的文件，不替你装依赖，也不会让已启动的程序重新读取代码。需要按项目说明安装和重启。
6. 工作目录、解释器选择、导入来源，以及资源读取规则。

### 实验挑战题

- **记录依赖版本**：保存经过审核的完整依赖解析结果／锁文件，并记录 Python 和平台。不要把带本机路径的未经审核 freeze 当通用配方。
- **离线准备**：Python 安装条件、兼容依赖 wheel、自身产物、非代码资源、系统组件来源；需要源码构建时还要构建工具链。最好先在断网的受控目标环境验证。
- **跨系统迁移**：检查原生包、系统 API、路径、大小写、编码、权限和启动脚本；目标环境重新安装，不搬旧 .venv。

## 五种项目的迁移思考练习

### 1. 只使用标准库的批量改名脚本

环境较简单，但风险主要是文件操作范围。应使用小型测试目录验证，明确输入目录，不拿真实重要文件做第一次实验。

### 2. 读取 Excel 的分析项目

要记录表格库版本、输入文件来源与格式、输出编码和路径。Notebook 还要记录内核，清空状态后按顺序执行。

### 3. Web 后端

除了 Python 依赖，还要准备数据库、配置、端口、服务启动和数据库迁移；开发调试服务器不自动等于生产部署方案。

### 4. 机器学习推理

除了代码，还要明确模型版本、权重来源、预处理规则、CPU/GPU 运行要求和驱动。相同包版本不能代替模型文件一致。

### 5. 桌面应用

需要界面运行库、系统 API、资源路径和平台测试。打包 exe 服务于终端用户，源码环境服务于开发，两者应分别验证。

## 毕业任务：写一份陌生项目接手报告

不要求长，但必须能让别人复现。按下面模板填写：

```text
项目用途：
源码版本／分支：
支持系统与 Python：
安装方案与依赖文件：
运行入口：
配置来源与必填项（不填秘密值）：
外部资源／服务：
输入、输出与个人数据位置：
最小验证命令：
完整验收步骤：
哪些内容进 Git，哪些不进：
换电脑时需要重建／复制／重新配置的内容：
当前已验证与尚未验证的范围：
```

写完后，让别人照着做：能否找到正确的 Python、装好依赖、准备文件并运行成功？哪里还需要口头解释，就把哪里的步骤写清楚。

## 最后的一组判断题

请先自行回答，再看括号中的结论。

- 只要有 pyproject.toml，所有项目都不再需要其他依赖文件。（错：取决于项目的锁定与安装方案。）
- 激活后安装包，就永远不会装错环境。（错：仍要看实际调用入口，尤其明确路径和编辑器。）
- 同一 wheel 能在任何 Python 和系统安装。（错：取决于兼容标签与依赖。）
- 标准库没有第三方安装需求，因此也不需要考虑 Python 版本。（错：标准库接口也受版本影响。）
- Git clone 会自动获取 Git 忽略的大模型。（错：需要另行准备，除非项目有明确机制。）
- 普通安装与可编辑安装都可以运行代码，但更新工作区后的行为不同。（对。）
- 一个程序没有图形窗口，就没有启动。（错：进程可在后台或命令行运行。）
- 能从源码目录外运行已安装的 wheel，是比只从源码启动更强的一项验证。（对，但仍不等于所有平台都验证过。）

遇到错误时，先判断是哪一步出了问题，再选办法修复。

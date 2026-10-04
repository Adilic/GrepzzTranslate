# 第三册：动手实验、故障案例与参考答案

[课程目录](README.md) · [第一册](01-runtime-and-environments.md) · [第二册](02-projects-and-reproducibility.md)

这一册把前两册的概念变成你能观察的事实。不要直接连续执行全部代码：先看当前目录和前提，预测结果，再运行，最后解释结果。

## 开始前：实验约定

以下以 Windows PowerShell、Python 3.12 为演示环境。`py -3.12` 应能启动该版本；如果找不到，应先准备对应基础 Python，而不是在已有重要项目里乱改环境。

实验使用你自己新建的学习目录，例如 `D:\PythonLearning`。不要求电脑一定有 D 盘；选择自己的目录即可。本文中的路径不是必须照抄的固定值。

准备一份学习记录，逐次填：

| 项目 | 记录什么 |
| --- | --- |
| 目标 | 这次想验证哪个概念 |
| 工作目录 | Get-Location 的结果 |
| 解释器 | sys.executable 的结果 |
| 预测 | 运行前认为会发生什么 |
| 实际 | 输出、退出码或文件变化 |
| 结论 | 哪个假设得到证明或被推翻 |

除了明确的故障实验，出现报错就先停下，不继续依赖失败步骤。Windows 文件扩展名最好设为可见，避免 hello.py 实际变成 hello.py.txt。

### 先认识实验中的少量语法

```python
name = "Python"
print(name)
```

第一行把字符串赋给变量，第二行调用打印函数。引号内是文字，不会被当成变量名。

```python
def greet(name):
    return "Hello " + name
```

def 定义函数，缩进表示函数体，return 返回结果。调用 `greet("Python")` 得到字符串；只定义函数不会自动调用它。

```python
from pathlib import Path
```

这表示从模块导入一个名字。pathlib 属于标准库，无须 pip 安装。

这些知识足够开始本册；先不要为了读懂工程实验补完所有 Python 语法。

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

### 推导

“我的脚本明明和配置文件放在一起，为什么找不到？”可能是代码使用了工作目录相对路径。

如果配置设计为脚本旁边的固定文件：

```python
config_path = Path(__file__).resolve().parent / "config.json"
```

如果配置应该由用户指定，就用命令行参数获取位置。不要一律把工作目录强行改成脚本目录，那可能改变其他输入输出的含义。

### 达标问题

你能否用一句话解释 Path.cwd() 与 `__file__` 的区别？不要只回答“一个短一个长”。

## 实验 2：观察虚拟环境身份与激活

### 目标

证明虚拟环境有自己的身份，同时理解激活只是选择命令入口的一种方式。

### 操作

回到你选定的 path-lab：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable); print(sys.prefix); print(sys.base_prefix)"
.\.venv\Scripts\python.exe -m pip --version
```

观察解释器是否在该环境中，prefix 和 base_prefix 是否不同，pip 输出的路径是否属于该环境。

再运行：

```powershell
.\.venv\Scripts\python.exe where_am_i.py
```

到这里没有激活，也已经使用了环境。因此“必须激活才能运行”是不成立的。

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

把课程中的 [textstats-kit 示例文件夹](examples/textstats-kit/README.md) 复制到独立学习目录，例如 `D:\PythonLearning\textstats-kit`。复制源文件即可，不搬其他项目的 .venv。若目标已存在，先确认它是否是自己已有的实验，不要盲目覆盖。

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

在没有额外 PYTHONPATH 等干扰的正常新环境中，预期提示找不到模块。源码在 src 下，新环境尚不知道这个包的安装关系。这一步故意失败，不说明示例坏了。

如果它反而成功，先检查解释器、sys.path、环境变量和导入文件位置；不要忽略这个出乎意料的结果。

### 安装后再运行

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m textstats_kit --demo
.\.venv\Scripts\textstats.exe --demo
.\.venv\Scripts\python.exe -c "import textstats_kit; print(textstats_kit.__file__)"
```

第一次安装需要获取开发工具及构建依赖，通常需要联网。业务示例本身没有第三方运行依赖。

`-e ".[dev]"` 的含义是：可编辑安装当前项目，同时选中 pyproject 中定义的 dev 可选依赖。它不是创建一个叫 dev 的新环境。

两个运行入口应输出相同统计内容。示例含两行文本，以空白分隔的 words 为 3。characters 包含换行；在正常文本读取的换行归一化下，本示例应为 21 个码点。

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

`str`、`dict[str, int]` 是类型标注，帮助读者和工具理解，不会自动把所有错误输入转换成正确类型。

`len(text)` 计算字符串的 Unicode 码点数，不是 UTF-8 字节数，也不总等于人眼看到的字形数。`split()` 按空白拆分；它不是中文分词算法。这里故意把统计定义写清楚，避免名称看似正确、语义却含糊。

再看 cli.py：它用 argparse 处理输入参数，用 pathlib 读外部文件，用 importlib.resources 读包内资源，最后把统计结果格式化成 JSON。

核心函数不知道终端长什么样，也不需要用户真的输入命令；所以容易独立测试。

### 证明“业务没有启动”与“导入已经发生”不同

```powershell
.\.venv\Scripts\python.exe -c "from textstats_kit import summarize; print(summarize('one two'))"
```

这直接调用函数，不经过命令行参数解析，也不会运行 `--demo`。同一份核心逻辑以后可被图形界面或 Web 接口调用。

### 修改练习

先把 README 里的一句话改成自己的描述，观察运行结果不会改变。再修改 cli.py 的帮助说明并执行 `--help`，观察可编辑安装下源码改动生效。

这一阶段不用改项目版本和入口名字。以后修改 pyproject 的命令入口映射时，需要重新安装项目才能重新生成入口。

## 实验 4：用测试明确输入输出的边界

### 目标

知道“运行过一次”与“验证了关键行为”的区别。

### 操作

仍在示例根目录：

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

随附 6 项测试：空字符串、空白与结尾换行、Unicode、外部文件、从无关目录读取包内示例、缺失文件的退出码。

### 为什么这几个测试有用

空文本是最容易被忽略的边界。结尾换行是否算额外空行需要定义。中文路径验证文件读写。切换工作目录测试暴露资源路径假设。缺文件验证程序能否明确失败，而不是输出伪造的空结果。

测试不应只是“函数被调用过”；它应说明什么行为是正确的。

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

先手算：a、换行、换行、b 是 4 个码点；中间有空行，因此是 3 行；空白分词得到 a、b 两个词。再运行测试验证。

### 学会读失败

在自己的学习副本中暂时把这个预期 lines 改成 2，再运行单个测试：

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_core.py::test_blank_line_is_counted -q
```

预期会失败，并显示实际值与预期值差异。理解错误后改回 3。这个故障实验不需要修改正式应用代码。

## 实验 5：制作 wheel，并在第二个环境验证

### 目标

证明项目能脱离“开发环境刚好有源码”的状态运行。

### 构建

仍在示例根目录，用开发环境执行：

```powershell
.\.venv\Scripts\python.exe -m build --wheel
```

构建过程可能建立临时构建环境并获取构建依赖。输出包含：

```text
dist/textstats_kit-0.1.0-py3-none-any.whl
```

wheel 的包名使用下划线，不代表 pyproject 的发行名写错。这种规范化属于打包命名过程。

### 第二环境普通安装

```powershell
py -3.12 -m venv .verify-venv
.\.verify-venv\Scripts\python.exe -m pip install --no-deps .\dist\textstats_kit-0.1.0-py3-none-any.whl
.\.verify-venv\Scripts\python.exe -c "import textstats_kit; print(textstats_kit.__file__)"
```

这里故意不用 `-e`，目的是安装构建产物。`--no-deps` 合理的前提是本教学包确实没有运行依赖；不能复制到任意项目而忽略其依赖。

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

Push-Location 保存旧目录并进入新目录；finally 保证退出实验后回到原目录。`-I` 使用 Python 隔离启动模式，减少用户环境和当前目录对导入的影响；它仍不是不可信代码的安全沙箱。

应仍然获得同样 JSON。这里同时验证了包代码、入口和非 Python 的 example.txt 确实能从安装产物中使用。

### 比较两种安装

| 观察 | .venv 可编辑安装 | .verify-venv 普通 wheel 安装 |
| --- | --- | --- |
| 导入来源 | 开发 src | 环境 site-packages |
| 修改工作区函数后重启 | 通常马上使用新函数 | 仍使用已安装版本 |
| 目的 | 开发迭代 | 验证交付产物 |

如果验证环境失败而开发环境成功，首先检查 wheel 漏文件、未声明依赖、错误路径和不同解释器，不要把开发目录临时加到验证环境 sys.path 来“修好”。那会破坏本次验证的目的。

## 实验 6：模拟第二台电脑，写出迁移清单

### 目标

把“复制文件夹”升级为“描述并恢复完整运行条件”。

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

然后考虑一个更复杂项目：如果它依赖数据库、模型、浏览器驱动或 GPU，逐项加入清单。环境描述不能只写“安装 Python”。

### 真正到第二台电脑时

开发方式：拿源码，在目标机器创建 .venv，按声明安装，再运行测试。交付方式：拿 wheel，在兼容解释器环境普通安装，再做产物验收。

不要搬第一台的 .venv。不要把一个 Windows 原生扩展 wheel 当成 Linux 通用包。也不要复制含个人密码的配置后再提交 Git。

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

**原因**：按独立脚本启动时，没有预期的包上下文。

**修复**：先安装项目，然后使用 `python -m 包名.模块名` 或声明的命令入口。不要为了消除错误随意删除相对导入中的点并追加多个路径。

### 案例 E：No matching distribution found

**可能原因**：版本拼写错误、当前 Python 太新／太旧、目标架构不支持、指定包源缺包，或仅允许 wheel 时没有对应产物。

**观察**：Python 版本、platform.machine()、pip 输出所访问的源、上游支持说明。网络超时与确实没有兼容版本不是同一件事。

**修复原则**：选择项目支持的解释器和版本组合。不要把“不支持的平台”通过不断重试变成“网络问题”。

### 案例 F：开发目录运行正常，wheel 安装后找不到 example.txt

**原因**：源码存在资源，但构建配置没有包含它，或者运行时用工作目录读取它。

**验证**：检查 wheel 内文件列表；从安装后的包使用 importlib.resources 读取。

**修复**：在构建配置中声明资源，并重新构建、重装、外目录验收。不是让用户把源码目录复制到 site-packages 旁边。

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

只有证明源文件、解释器和运行进程都一致后，才考虑更底层的缓存和打包问题。

### 案例 I：Git 已提交，另一台仍看不到

**区别**：保存文件 ≠ add ≠ commit ≠ push；另一台还需要 fetch／pull 并处于正确分支。

先看两台提交号和分支，再看远端。不要直接复制整个 .git 文件夹去覆盖另一个仓库。

### 案例 J：激活虚拟环境后仍无法安装系统组件

**原因**：虚拟环境管理的是 Python 环境，不是系统管理员权限，也不是操作系统包管理器。

需要系统库、驱动或可选组件时按该组件说明准备。反过来，普通项目的 Python 依赖通常应安装到自己可写的环境，不应一遇到失败就用管理员权限全局安装。

## 检查题参考答案

### 第一册

1. 普通相对文件路径基于工作目录，不保证基于脚本位置。不同启动目录可导致读取不同文件。
2. 不会。已经启动的 B 进程有自己的解释器与环境状态；改变另一个 shell 的激活状态不能替换它。
3. 是，都是让选定解释器按模块方式执行，只是模块分别是 pip 和业务模块。
4. import 可能在测试、其他模块或工具运行时发生；无条件网络请求会产生副作用、延迟与失败。把操作放在明确调用的函数里。
5. 发行包名与导入包名由项目定义，不要求完全相同。
6. venv 不隔离账号文件权限和网络访问，不是安全执行边界。

### 第二册

1. 源码目录可能有构建未包含的资源，开发环境也可能装有未声明依赖。普通安装后的行为要独立验证。
2. 应用希望固定自己部署的环境；库要与使用者其他依赖共存，通常表达兼容范围。同时仍可在库自己的测试中固定或覆盖多个版本组合。
3. requirements 提出安装需求；constraints 约束解析范围，单独列出不意味着一定安装。
4. Python、平台、系统组件、驱动、配置、资源、数据和外部服务都可能不同。
5. pull 只更新版本控制文件，不安装包，也不重新加载已运行进程。依赖和代码需要按更新要求同步与重启。
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

这些例子用来练习分类，而不是提供各领域完整部署教程。能识别需要补充哪些条件，就是通用工程基础的价值。

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

评分标准不是术语多少，而是：别人是否能按报告定位正确解释器、装好环境、找到入口、准备资源并验证结果。

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

完成这册后，你应能先判断“问题属于哪一层”，再选择工具处理，而不是遇到任何错误都重装 Python。

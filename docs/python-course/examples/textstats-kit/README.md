# textstats-kit：Python 工程教学项目

这是独立的学习例子。运行只需 Python 自带的标准库；开发时再安装 pytest（测试）和 build（打包）。先复制这个文件夹到学习目录，再操作，避免改到正式应用环境。

它读取 UTF-8 文本，输出三项结果：characters 按 Python 的码点计数，包含换行；lines 按 splitlines() 数行；words 按空白拆分计数。因此 words 不是中文、日文的真实词数，characters 也不一定等于肉眼看到的字数。

在复制后的文件夹中打开 PowerShell，应能看到 pyproject.toml。下面六条依次是：建环境、安装开发所需内容、两种方式运行示例、测试、打包。逐条执行，报错先停下。初次安装通常需要联网。

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m textstats_kit --demo
.\.venv\Scripts\textstats.exe --demo
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build --wheel
```

两次运行都应得到 characters=21、lines=2、words=3；测试应显示 `6 passed`。要读取自己的文件，把下面路径换成实际存在的 UTF-8 文本路径：

```powershell
.\.venv\Scripts\python.exe -m textstats_kit --input "D:\Learning\input.txt"
```

相对路径从当前工作目录开始找；--demo 则读取包内示例，不受工作目录影响。--input 和 --demo 每次只能选一个。文件不存在或编码不对时，程序会报错并返回非零退出码。

构建产物为 `dist/textstats_kit-0.1.0-py3-none-any.whl`。这个示例的 wheel 是纯 Python 包，不代表所有项目都能使用同样的兼容标记。

创建第二环境并普通安装 wheel，可验证它不再依赖开发源码：

```powershell
py -3.12 -m venv .verify-venv
.\.verify-venv\Scripts\python.exe -m pip install --no-deps .\dist\textstats_kit-0.1.0-py3-none-any.whl
.\.verify-venv\Scripts\python.exe -I -m textstats_kit --demo
```

逐步讲解见[第三册](../../03-labs-and-troubleshooting.md)。本例只需在本地学习、安装，无需发布到 PyPI。

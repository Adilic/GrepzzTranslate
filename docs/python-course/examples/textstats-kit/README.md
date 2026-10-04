# textstats-kit：Python 工程教学项目

这个例子独立于 GrepzzTranslate。业务运行只使用 Python 标准库，开发阶段使用 pytest 和 build。建议复制此文件夹到自己的学习目录再修改；不要向 GrepzzTranslate 的应用环境安装教学项目。

它读取 UTF-8 文件，输出 JSON：characters 为 Python 字符串的 Unicode 码点数量（包括换行），lines 使用 splitlines 的行计数，words 使用空白分隔。中文、日文不做语言分词；字形、字节、码点也不是同一个概念。

在本目录中：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m textstats_kit --demo
.\.venv\Scripts\textstats.exe --demo
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m build --wheel
```

读取自己的文件：

```powershell
.\.venv\Scripts\python.exe -m textstats_kit --input "D:\Learning\input.txt"
```

路径按工作目录解释；--demo 的内容来自包内资源，不依赖工作目录。`--input` 与 `--demo` 必须且只能选一个。缺文件或编码不正确时返回非零退出码，错误输出到标准错误流。

构建产物为 `dist/textstats_kit-0.1.0-py3-none-any.whl`。这个示例的 wheel 是纯 Python 包，不代表所有项目都能使用同样的兼容标记。

创建第二环境并普通安装 wheel，可验证它不再依赖开发源码：

```powershell
py -3.12 -m venv .verify-venv
.\.verify-venv\Scripts\python.exe -m pip install --no-deps .\dist\textstats_kit-0.1.0-py3-none-any.whl
.\.verify-venv\Scripts\python.exe -I -m textstats_kit --demo
```

更多逐步解释、故意制造的错误与参考答案见课程第三册。不要上传此教学示例到 PyPI；安装本地 wheel 足以完成实验。

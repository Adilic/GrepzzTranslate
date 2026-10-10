# 日中小模型实测（2026-10-10）

## 当前结论

本次比较八个小型候选。LFM2-350M 的短句表现最好，已直接接入主项目和日常 EXE，但复杂否定仍会出错，不能声称日语翻译问题已经全面解决。按用户要求，统一在主项目中开发和测试，日常程序为 `dist/GrepzzTranslate/GrepzzTranslate.exe`，独立试验 EXE 已删除；旧资源暂留 build/ 缓存，不再运行或参与打包。

LFM 权重约 229 MB，配上 Windows CPU 运行文件、许可和元数据，日英资源目录共 262,687,247 字节（约 263 MB）；还需已有英中模型。这不等于整个应用的大小。它采用 LFM Open License v1.0，属于开放权重许可，不是 Apache/MIT。用户已要求直接在主项目中使用和测试；上述许可及质量限制仍然适用。

## 为什么没有选最小的模型

大小为本地使用或评估的权重文件，以十进制 MB 取整。结果来自真实推理，没有针对示例写死答案。这里只比较少量阅读句子，不是完整基准排名。

| 候选与来源 | 权重约大小 | 许可说明 | 实测主要问题 |
|---|---:|---|---|
| [Mitsua ELAN tiny](https://huggingface.co/Mitsua/elan-mt-tiny-ja-en)，INT8 | 16 MB | CC-BY-SA 4.0 | 「けなさない」译为 don't hurt yourself；关键动词错误 |
| [Mitsua ELAN BT](https://huggingface.co/Mitsua/elan-mt-bt-ja-en)，INT8 | 62 MB | CC-BY-SA 4.0 | 同样混淆贬低与伤害，部分表达改变语气 |
| [FuguMT](https://huggingface.co/staka/fugumt-ja-en)，INT8 | 62 MB | CC-BY-SA 4.0 | 「けなさない」译为 don't deceive yourself |
| [opus-mt-ja-zh](https://huggingface.co/shun89/opus-mt-ja-zh)，INT8 | 80 MB | 模型卡标注 Apache-2.0，训练说明较少 | 出现“不欺骗自己”“不要把自己放在一边” |
| [SMaLL-100](https://huggingface.co/alirezamsh/small100)，[第三方 INT8](https://huggingface.co/luonluonvn/small100_ct2_quant_int8) | 339 MB | 原模型 MIT；第三方转换缺少充分许可说明 | 「けなす」仍译成伤害；未采用此分发资源 |
| [Qwen3-0.6B Q4_K_M](https://huggingface.co/unsloth/Qwen3-0.6B-GGUF) | 397 MB | Apache-2.0 | 有时原样返回日文，出现严重动词误译 |
| [Qwen3.5-0.8B Q4_K_M](https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF) | 533 MB | Apache-2.0 | 「けなさない」仍译成不要让自己受伤；部分提示下丢失否定 |
| [LFM2-350M-ENJP-MT Q4_K_M](https://huggingface.co/LiquidAI/LFM2-350M-ENJP-MT-GGUF) | 229 MB | LFM Open License v1.0，含商业营收限制 | 短句改善明显，但长句会把复杂否定译反；已接入主程序，仍有已知误译 |

Marian 候选使用独立评估环境转换为 CTranslate2 INT8。转换时保留实际解码起始嵌入，并禁止生成 pad token，避免把错误转换的结果当作模型质量。GGUF 候选使用官方 llama.cpp CPU 运行文件。尝试过不同提示词及自然标点，未通过为「けなす」写特例替换来制造正确结果。

## LFM 的实际结果

日语先译成英语，再使用现有 Argos 英中模型生成中文。因此既有日英误差，也可能有第二步中转误差。

| 原文 | 最终中文实际输出 | 判断 |
|---|---|---|
| 自分をけなさない | - 我不会小看自己。 | 贬低的含义保留；人称和语气不一定符合上下文 |
| 自分をけなさないでください。 | 请不要轻视自己。 | 大意正确 |
| 他人と自分を比べない。 | 我不会把自己和别人比起来 | 否定保留；语气可能有偏差 |
| 失敗しても、自分を責める必要はありません。 | 如果你失败了 你不必责怪自己 | 大意保留，让步关系有所弱化 |
| 彼は私をけなした。 | 他鄙视我 | 含义接近，表达仍有偏差 |
| この薬を飲んではいけません。 | 你不该吃这种药 | 否定保留 |
| まだ読み終わっていません。 | 我还没读完呢 | 大意正确 |
| 今日はいい天気です。 | 今天天气不错 | 大意正确 |

**必须保留的反例**：关于本书致谢的长句包含「現実から目をそむけずに世の中と関わっていく」，意思是“不逃避现实，参与这个世界”。模型却输出英语 `staying away from reality`，最终成为“远离现实”，否定被译反。拆成两句重试仍未解决。此已知问题仍未解决，接入主程序不代表翻译质量已全面达标。

短句在本开发机完整日中流程通常约 0.6～0.8 秒，首次约 1.7 秒；上述长段落约 1.6 秒。不包括 OCR 和用户操作，也不代表其他电脑的速度。

## 来源和本地执行方式

- 官方 GGUF 仓库固定版本 `889c88c3d3681b4f342ae210a1d2a1369aba0e10`，文件 `LFM2-350M-ENJP-MT-Q4_K_M.gguf`。
- 权重 229,310,240 字节；SHA256：`574ef7980dd20d69b494bce82565db5f25124d404be02052bbca62277d33077b`。
- 运行文件来自 [llama.cpp b11540 官方发行](https://github.com/ggml-org/llama.cpp/releases/tag/b11540)，CPU x64 ZIP SHA256：`85cae1b982145d1b315e56e7343524b301a11f0fdf2c7c9dd973c26daba4b3b5`。
- 安装脚本校验完整下载，保留原始模型许可、运行库许可和文件来源散列；不执行 Hugging Face 仓库内的 Python 代码。散列确认文件一致性，不是安全认证。
- 运行时调用隐藏的本地进程，强制离线，不启动 HTTP 或 RPC 服务，不需要 PyTorch 或 Ollama。当前每次调用会加载模型，计时包含这个开销。
- LFM 许可含商业营收限制，完整文本见 [固定版本 LICENSE](https://huggingface.co/LiquidAI/LFM2-350M-ENJP-MT-GGUF/blob/889c88c3d3681b4f342ae210a1d2a1369aba0e10/LICENSE)。项目源码许可和模型许可是两件事。

## 应用验收与迁移

74 项自动测试通过，其中 5 项使用真实可选模型，覆盖短句关键含义、否定、原文和读音保留；不能据此推断任意长句翻译正确。

主程序 EXE 完成 7 个截图样本、4 个 Alt+1 划词样本，检查结果显示、日语注音、剪贴板恢复、点击外部关闭和后台存活。报告为 `dist/GrepzzTranslate/logs/self-test.json`。未覆盖 Chrome PDF 的实际复制限制、其他 Windows 版本或多屏环境。

直接使用项目根目录原来的启动快捷方式即可，无需切换版本。**复杂否定仍有已知误译，判断关键含义时请核对原文。**

Git 同步代码、安装脚本、文档和测试；`build/`、`dist/`、模型权重、评估环境、个人配置、历史与日志不上传。接受模型许可后，第二台电脑可以运行 `scripts/install_japanese_model.py`，或复制完整 `resources/translation/ja_en_lfm/` 和已有 `en_zh/`。其他失败候选均为开发机的忽略缓存，不进入发行包。

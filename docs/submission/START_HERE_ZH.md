# RRA 提交包快速入口

## 成品

- `RRA_Submission.pptx`：12 页可编辑演示文稿。
- `RRA_Submission.pdf`：对应 PDF；附每页 PNG 预览。
- `Formal_Results.png` / `.svg`：正式对比图，标明 TIEBREAK 四种文本条件下不安全事件范围为 58–59。
- `RRA_Demo.mp4`：完整英文旁白视频、动态真实开发轨迹演示、烧录字幕。
- `RRA_Demo.srt`、`Transcript_EN.txt`、`Transcript_ZH.txt`、`Demo_Script.md`：字幕和双语脚本。
- `demo_viewer.html`：单文件离线 B3 开发轨迹查看器。
- `RRA_Submission_Package.zip`：含成品、README/runbooks、构建源和输入包；根目录含 `START_HERE_ZH.md` 与内部 `PAYLOAD_SHA256SUMS.txt`。
- `Submission_Text_EN.md` / `Submission_Text_ZH.md`：可直接粘贴的双语项目文稿；另附集成说明、限制披露、来源索引和官方要求矩阵。
- `SHA256SUMS.txt`：外部文件校验和；另有 `build_only/` 原始完整旁白 WAV 与 `scene_audio_timing.json` 供审查，不装入 ZIP。

## 事实范围

项目是二维输送带仿真研究原型。STRICT 按构造等于 B3；TIEBREAK 未显示恢复收益。视频中的 14 步轨迹、7 个 picked、5 个 escalated 是新鲜 B3 开发证据，不是正式 eval-v3 结果。Meterless 开发检查和 Zetaris 等价回执的角色与边界见 `Integration_Explanation.md` 和 `Evidence_Source_Index.md`。

## 从干净解压目录重新构建

先安装系统要求：Python 3.12、ffmpeg/ffprobe（含 flite 滤镜）、DejaVu Sans 字体。然后：

```bash
python -m venv .venv
.venv/bin/pip install -r source/requirements-material.txt
.venv/bin/python source/build_submission.py --output-dir ./rebuilt_submission
node source/validate_viewer.mjs ./rebuilt_submission/demo_viewer.html
```

构建器只读取 `source/data/` 和 `source/source_docs/` 中的捆绑文件。不会访问本仓库控制目录、报告目录、模型 API、Docker 或 Meterless 服务。`build_only/` 留存原始旁白和每段时序，以便检查旁白未被截断。

## 仍需所有者完成

确认注册团队身份和个人参与事实；仅在需要提及 Cursor 时确认实际使用；填写所有者专属官方表单字段、选择提交账号并提交。本包不宣称已发布或已提交。

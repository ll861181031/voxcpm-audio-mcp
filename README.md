# VoxCPM Audio MCP

本地语音与歌声合成 MCP 服务，把已经安装好的 **VoxCPM2** 和 **SoulX-Singer** 暴露给支持 MCP 的客户端。

## 功能

- `speak`：用 VoxCPM2 生成普通语音、情感旁白或参考音色克隆。
- `speak_segments`：把多段文字分别合成，再按设定停顿拼接成完整旁白。
- `sing_metadata`：用 SoulX-Singer 读取目标元数据并生成歌声。
- `sing_notes`：直接输入音素、MIDI 音高和每字时长生成歌声。
- `health`：检查模型路径、FFmpeg、VoxCPM2 服务和 GPU 显存。

服务只返回本地音频文件路径，不包含模型权重。

## 前置条件

- Windows 10/11
- Python 3.10+
- 已安装 VoxCPM2 本地服务，默认 `D:\Desktop\VoxCPM2`
- 已安装 SoulX-Singer，默认 `D:\Desktop\SoulX-Singer`
- 可用 FFmpeg，默认 `D:\Desktop\VoxCPM2\tools\ffmpeg\bin\ffmpeg.exe`
- NVIDIA GPU 或使用 `device=cpu`

## 安装

```powershell
cd C:\Users\lsr\Documents\Codex\2026-09-16\yan\outputs\voxcpm-audio-mcp
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\install.ps1
```

安装脚本会创建独立 `.venv`，不会修改系统 Python。

## 配置

复制 `.env.example` 为 `.env`，按本机路径修改。也可以直接设置环境变量。

关键变量：

```text
VOXCPM_URL=http://127.0.0.1:8808
VOXCPM_START_SCRIPT=D:\Desktop\VoxCPM2\Start-VoxCPM.ps1
SOULX_HOME=D:\Desktop\SoulX-Singer
SOULX_MODEL_PATH=D:\Desktop\SoulX-Singer\pretrained_models\SoulX-Singer\model.pt
FFMPEG=D:\Desktop\VoxCPM2\tools\ffmpeg\bin\ffmpeg.exe
MIN_FREE_VRAM_MB=6000
```

## 启动 MCP

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run.ps1
```

或者直接运行：

```powershell
.\.venv\Scripts\python.exe -m voxcpm_audio_mcp.server
```

该服务使用 stdio transport，适合由 Codex、Claude Desktop 或其他 MCP 客户端启动。

## Codex MCP 配置示例

参见 [examples/mcp_config.json](examples/mcp_config.json)：

```json
{
  "mcpServers": {
    "voxcpm-audio": {
      "command": "C:\\Users\\lsr\\Documents\\Codex\\2026-09-16\\yan\\outputs\\voxcpm-audio-mcp\\.venv\\Scripts\\python.exe",
      "args": ["-m", "voxcpm_audio_mcp.server"],
      "env": {
        "VOXCPM_HOME": "D:\\Desktop\\VoxCPM2",
        "SOULX_HOME": "D:\\Desktop\\SoulX-Singer",
        "FFMPEG": "D:\\Desktop\\VoxCPM2\\tools\\ffmpeg\\bin\\ffmpeg.exe"
      }
    }
  }
}
```

## 工具示例

### 普通说话

```json
{
  "text": "你好呀，今天也要开开心心的哦。",
  "control_instruction": "年轻可爱女声，清亮甜美，亲切自然，带一点笑意。",
  "cfg_value": 2.2,
  "inference_timesteps": 14,
  "output_format": "mp3"
}
```

### 分段情感旁白

```json
{
  "segments": [
    {
      "text": "一九三四年十月，赣南秋风卷着细雨。",
      "control_instruction": "低沉凝重，缓缓追忆。",
      "pause_ms": 900
    },
    {
      "text": "这一送，是百姓的不舍。",
      "control_instruction": "深情、克制，句尾放慢。",
      "pause_ms": 1200
    }
  ],
  "cfg_value": 2.3,
  "inference_timesteps": 16
}
```

### 按音符唱歌

`phonemes`、`note_pitches` 和 `durations_ms` 必须一一对应。`<SP>` 表示停顿。

```json
{
  "phonemes": [
    "<SP>",
    "zh_yi1", "zh_shan3", "zh_yi1", "zh_shan3",
    "zh_liang4", "zh_jing1", "zh_jing1",
    "<SP>",
    "zh_man3", "zh_tian1", "zh_dou1", "zh_shi4",
    "zh_xiao3", "zh_xing1", "zh_xing1"
  ],
  "note_pitches": [0, 60, 60, 67, 67, 69, 69, 67, 0, 65, 65, 64, 64, 62, 62, 60],
  "durations_ms": [200, 350, 350, 350, 350, 350, 350, 500, 300, 350, 350, 350, 350, 350, 350, 600],
  "text": "<SP> 一 闪 一 闪 亮 晶 晶 <SP> 满 天 都 是 小 星 星",
  "device": "auto"
}
```

## 显存策略

- `speak` 需要 VoxCPM2 服务，默认占用约 8GB 显存。
- `sing_notes` 在 `device=auto` 时，如果可用显存低于 `MIN_FREE_VRAM_MB`，会自动回退到 CPU。
- 强制 `device=cuda` 时，显存不足会直接报错，不会抢占正在运行的任务。
- VoxCPM2 和 SoulX-Singer 不建议同时常驻。当前 12GB 显卡上建议串行调用。

## 安全与合规

- 只处理本地文件，不自动上传音频或文本。
- 参考音频和音色克隆仅用于本人声音或已获授权的声音。
- 不包含模型权重，模型需由用户自行安装和确认许可证。
- MCP 默认通过 stdio 运行，不开放网络端口。

## 开发与测试

```powershell
uv pip install -e ".[dev]"
.\.venv\Scripts\python.exe -m pytest
```

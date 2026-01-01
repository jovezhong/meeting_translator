# Meeting Translator 使用指南

本文档提供详细的使用说明和最佳实践。

---

## 目录

- [安装指南](#安装指南)
- [基本使用](#基本使用)
- [高级配置](#高级配置)
- [故障排除](#故障排除)
- [最佳实践](#最佳实践)

---

## 安装指南

### Windows 平台

#### 1. 安装 Python

1. 下载 [Python 3.9-3.11](https://www.python.org/downloads/)
2. 安装时勾选 "Add Python to PATH"
3. 验证安装：
   ```bash
   python --version
   ```

#### 2. 安装 Voicemeeter

1. 访问 [Voicemeeter 官网](https://voicemeeter.com/)
2. 下载 Voicemeeter Banana 或 Potato 版本
3. 运行安装程序并按提示完成安装
4. 安装完成后**重启电脑**

#### 3. 验证 Voicemeeter 安装

打开 Windows 声音设置：
- 录音设备：应该看到 "Voicemeeter Output" 或 "VoiceMeeter Output"
- 播放设备：应该看到 "Voicemeeter Input" 或 "VoiceMeeter Input"

#### 4. 安装项目依赖

```bash
# 克隆项目
git clone https://github.com/eerenyuan/meeting_translator.git
cd meeting_translator

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 如果 PyAudio 安装失败，使用 pipwin
pip install pipwin
pipwin install pyaudio
```

#### 5. 配置 API Key

```bash
# 复制配置模板
copy .env.example .env

# 编辑 .env 文件
notepad .env
```

填入你的阿里云 API Key：
```
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxx
```

---

## 基本使用

### 启动程序

```bash
# 方法1: 使用批处理文件（推荐）
run.bat

# 方法2: 手动运行
# 1. 激活虚拟环境（如果使用）
.venv\Scripts\activate

# 2. 进入目录并运行
cd meeting_translator
python main_app.py
```

### 界面说明

程序启动后会显示主界面：

```
┌─────────────────────────────────────┐
│  Meeting Translator                 │
│  实时会议翻译系统                     │
├─────────────────────────────────────┤
│  当前模式: 说模式 (ZH→EN)            │
│  状态: 运行中                        │
│  延迟: <500ms                        │
├─────────────────────────────────────┤
│  快捷键:                            │
│    F1 - 切换到说模式                 │
│    F2 - 切换到听模式                 │
│    ESC - 退出程序                    │
└─────────────────────────────────────┘
```

### 模式说明

#### 说模式（Speak Mode）

**用途**: 将你的中文翻译成英文发给其他参会者

**操作步骤**:
1. 按 `F1` 切换到说模式
2. 在会议软件中设置麦克风为 "Voicemeeter Input"
3. 直接说中文
4. 其他参会者听到流畅的英文

**工作流程**:
```
你说中文 → 实时翻译 → 英文语音 → 虚拟麦克风 → 会议软件 → 其他人听到英文
```

#### 听模式（Listen Mode）

**用途**: 将其他人说的英文翻译成中文字幕

**操作步骤**:
1. 按 `F2` 切换到听模式
2. 确保系统音频输出正常
3. 看屏幕上的中文字幕

**工作流程**:
```
对方说英文 → 会议软件 → 系统音频 → 实时翻译 → 中文字幕显示
```

---

## 高级配置

### 调整 VAD 参数

编辑 `.env` 文件：

```bash
# VAD 阈值 (0.0-1.0)
# 较高的值 = 不容易触发，但可能漏掉轻声
# 较低的值 = 容易触发，但可能误识别噪音
VAD_THRESHOLD=0.5

# 静音检测时间 (毫秒)
# 停顿多久后认为句子结束
# 较短 = 响应快，但可能截断长句
# 较长 = 不易截断，但响应慢
SILENCE_DURATION_MS=800

# 前置缓冲 (毫秒)
# 捕获语音开始前的音频
# 避免句首被截断
PREFIX_PADDING_MS=300
```

### 调整语音参数

```bash
# TTS 语速 (1-5)
# 1 = 很慢，5 = 很快
# 推荐 4
TTS_RATE=4

# TTS 音调 (0.5-2.0)
# 1.0 = 正常音调
TTS_PITCH=1.0

# TTS 音量 (0-100)
TTS_VOLUME=50

# 声音选择
# 可选: Cherry, Ava, Emma, Brian, Andrew
TTS_VOICE=Cherry
```

### 自定义术语库

编辑 `meeting_translator/glossary.json`：

```json
{
  "description": "Translation glossary for meeting translator",
  "glossary": {
    "你的公司名": "Your Company Name",
    "产品A": "Product A",
    "业务系统": "Business System",
    "张总": "Mr. Zhang",
    "核心功能": "Core Feature"
  }
}
```

详细说明：[词汇表使用指南](GLOSSARY_GUIDE.md)

---

## 故障排除

### 问题 1: 无法启动程序

**症状**: 双击运行后立即关闭，或显示错误

**可能原因**:
- Python 未安装或版本不对
- 虚拟环境未激活
- 依赖包未安装

**解决方案**:
```bash
# 检查 Python 版本
python --version  # 应该是 3.9-3.11

# 激活虚拟环境
.venv\Scripts\activate

# 重新安装依赖
pip install -r requirements.txt --force-reinstall
```

### 问题 2: API Key 错误

**症状**: 程序显示 "API Key 无效" 或连接失败

**解决方案**:
1. 确认 `.env` 文件存在
2. 检查 API Key 是否正确复制（没有多余空格）
3. 验证 API Key 是否有效：
   - 登录 [阿里云控制台](https://dashscope.console.aliyun.com/)
   - 查看 API Key 状态
   - 确认余额充足

### 问题 3: 音频设备问题

**症状**: 找不到 Voicemeeter 设备

**解决方案**:
1. 重新安装 Voicemeeter
2. 重启电脑
3. 在 Windows 声音设置中启用被禁用的设备

### 问题 4: 翻译延迟高

**症状**: 说完很久才有翻译

**可能原因**:
- 网络延迟
- VAD 参数设置不当

**解决方案**:
```bash
# 降低 VAD 阈值
VAD_THRESHOLD=0.3

# 缩短静音检测时间
SILENCE_DURATION_MS=500
```

### 问题 5: 会议软件听不到翻译

**症状**: 说模式下，对方听不到声音

**检查清单**:
- [ ] 会议软件的麦克风设置为 "Voicemeeter Input"
- [ ] Voicemeeter 正常运行
- [ ] 程序显示"说模式"已激活
- [ ] 系统音量未静音

---

## 最佳实践

### 1. 会议前准备

**提前 5 分钟**:
- [ ] 启动程序，测试音频
- [ ] 说几句话，确认翻译正常
- [ ] 调整音量和语速
- [ ] 准备好术语库

### 2. 说话技巧

**为了获得最佳翻译效果**:
- ✅ 语速适中，吐字清晰
- ✅ 避免连续说话超过 1 分钟（给翻译时间）
- ✅ 重要术语提前加入词汇表
- ❌ 不要说话太快或含糊
- ❌ 避免中英文混杂

### 3. 网络要求

**推荐配置**:
- 带宽: 下行 5Mbps+，上行 2Mbps+
- 延迟: <100ms
- 稳定性: 无频繁掉线

**不推荐**:
- 移动热点
- 公共 WiFi
- VPN（可能增加延迟）

### 4. 多人会议

**说模式**:
- 你说中文，所有人听到英文
- 适合你主讲的场景

**听模式**:
- 所有人说英文，你看中文字幕
- 适合你主要倾听的场景

**灵活切换**:
- 用 F1/F2 快捷键随时切换
- 不影响会议进行

### 5. 隐私保护

**注意事项**:
- 所有翻译通过阿里云 API 处理
- 不会存储会议内容
- API 调用受阿里云隐私政策保护
- 敏感会议建议自建翻译服务

---

## 性能优化

### 降低延迟

1. **使用有线网络**
   - 避免 WiFi 波动

2. **关闭不必要的程序**
   - 释放CPU和内存

3. **优化 VAD 参数**
   ```bash
   VAD_THRESHOLD=0.4
   SILENCE_DURATION_MS=600
   ```

### 提高准确性

1. **维护术语库**
   - 提前录入专业术语
   - 定期更新

2. **清晰发音**
   - 标准普通话
   - 避免方言

3. **控制语速**
   - 不要太快
   - 适当停顿

---

## 键盘快捷键

| 快捷键 | 功能 |
|--------|------|
| F1 | 切换到说模式（中译英） |
| F2 | 切换到听模式（英译中） |
| ESC | 退出程序 |

---

## 支持的会议软件

| 软件 | 说模式 | 听模式 | 备注 |
|------|--------|--------|------|
| Zoom | ✅ | ✅ | 完全支持 |
| Microsoft Teams | ✅ | ✅ | 完全支持 |
| Google Meet | ✅ | ✅ | 完全支持 |
| 腾讯会议 | ✅ | ✅ | 完全支持 |
| Webex | ✅ | ✅ | 完全支持 |
| 钉钉 | ✅ | ✅ | 完全支持 |
| 飞书 | ✅ | ✅ | 完全支持 |
| Skype | ✅ | ✅ | 完全支持 |

**原理**: 系统在音频层面工作，与具体会议软件无关。

---

## 下一步

- [词汇表使用指南](GLOSSARY_GUIDE.md)
- [API 文档](API.md)
- [贡献指南](../CONTRIBUTING.md)

---

如有问题，请提交 [Issue](https://github.com/eerenyuan/meeting_translator/issues)

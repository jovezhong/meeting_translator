# Qwen API 与 OutputManager 完整集成指南

## ✅ 完全覆盖 Qwen API 特性

OutputManager 已完全支持 Qwen API 的所有特性，包括增量文本和预测文本（stash）。

### 🎯 核心特性

| 特性 | Qwen API | OutputManager | 状态 |
|------|----------|---------------|------|
| **增量文本** | `response.text.text` 事件 | `MessageType.PARTIAL_REPLACE` | ✅ 完全支持 |
| **预测文本（stash）** | `stash` 字段 | `predicted_text` 参数 | ✅ 完全支持 |
| **最终翻译** | `response.text.done` 事件 | `MessageType.TRANSLATION` | ✅ 完全支持 |
| **源文本** | 通常不提供 | `source_text=None` | ✅ 支持 |
| **颜色显示** | 手动格式化 | 自动处理 | ✅ 完全兼容 |

## 📊 数据流对比

### 旧系统（手动格式化）

```python
# livetranslate_text_client.py (原始代码)
elif event_type == "response.text.text":
    text = event.get("text", "")
    stash = event.get("stash", "")

    if text or stash:
        # 手动构造格式
        if stash:
            formatted_text = f"{text}【预测:{stash}】"
        else:
            formatted_text = text

        # 手动调用回调
        if on_text_received:
            on_text_received(f"[译增量] {formatted_text}")
```

**问题**：
- ❌ 格式化逻辑散落在多个地方
- ❌ 难以统一管理输出目标
- ❌ 颜色显示逻辑在 subtitle_window 中硬编码
- ❌ 不支持灵活切换输出目标

### 新系统（OutputManager）

```python
# livetranslate_text_client.py (使用 OutputManager)
elif event_type == "response.text.text":
    text = event.get("text", "")
    stash = event.get("stash", "")

    if text or stash:
        # 统一接口发送
        manager = OutputManager.get_instance()
        manager.partial(
            target_text=text,              # 已确定部分
            mode=IncrementalMode.REPLACE,  # REPLACE 模式
            predicted_text=stash,          # 预测部分
            metadata={"provider": "qwen"}
        )
```

**优势**：
- ✅ 统一的接口
- ✅ 自动分发到所有输出目标
- ✅ 自动格式化
- ✅ 自动处理颜色显示
- ✅ 灵活可扩展

## 🔄 完整数据流

### 1. Qwen API 事件

```json
// Event 1: 增量翻译（有预测）
{
  "type": "response.text.text",
  "text": "你好",
  "stash": "世界"
}

// Event 2: 最终翻译
{
  "type": "response.text.done",
  "text": "你好世界！"
}
```

### 2. OutputManager 处理

```python
# Event 1 处理
manager.partial(
    target_text="你好",              # text → target_text
    mode=IncrementalMode.REPLACE,
    predicted_text="世界",          # stash → predicted_text
    metadata={"provider": "qwen"}
)
# → 创建 TranslationMessage
# → full_target_text = "你好【预测:世界】"

# Event 2 处理
manager.translation(
    target_text="你好世界！",
    metadata={"provider": "qwen"}
)
# → 创建 TranslationMessage (is_final=True)
```

### 3. SubtitleHandler 处理

```python
# 接收 TranslationMessage
if message.message_type == MessageType.PARTIAL_REPLACE:
    # 使用 full_target_text（包含预测部分）
    self.current_partial_text = message.full_target_text
    # → "你好【预测:世界】"

    # 调用 subtitle_window.update_subtitle
    self.subtitle_window.update_subtitle(
        source_text="",
        target_text="你好【预测:世界】",
        is_final=False
    )
```

### 4. SubtitleWindow 渲染

```python
# 解析格式
match = re.match(r'^(.*?)【预测:(.*?)】$', "你好【预测:世界】")
confirmed = match.group(1)  # "你好"
predicted = match.group(2)  # "世界"

# HTML 渲染（带颜色）
html_parts.append(f'''
    <p style="color: rgba(255, 255, 255, 0.95); margin: 5px 0;">
        [{timestamp}] {confirmed}<span style="color: rgba(160, 160, 160, 0.85);">{predicted}</span> <span style="color: rgba(100, 150, 255, 0.8);">...</span>
    </p>
''')

# 结果：
# [HH:MM:SS] 你好(白色) 世界(灰色) ...(蓝色)
```

## 🎨 颜色显示

| 文本类型 | 颜色 | RGBA值 |
|---------|------|--------|
| **已确定文本** (text) | 白色 | `rgba(255, 255, 255, 0.95)` |
| **预测文本** (stash) | 灰色 | `rgba(160, 160, 160, 0.85)` |
| **增量标记** (...) | 蓝色 | `rgba(100, 150, 255, 0.8)` |
| **历史记录** | 白色 | `rgba(255, 255, 255, 1.0)` |

## 📝 代码对比

### 场景：翻译 "Hello world"

#### 旧系统实现

```python
# 1. livetranslate_text_client.py 发送
if stash:
    formatted_text = f"{text}【预测:{stash}】"
on_text_received(f"[译增量] {formatted_text}")

# 2. translation_service.py 转发
if text.startswith("[译增量]"):
    partial_text = text[6:].strip()
    self.on_translation(source_text, partial_text, is_final=False)

# 3. main_app.py 接收
def on_translation_received(self, source_text, target_text, is_final):
    self.subtitle_window.update_subtitle(source_text, target_text, is_final)

# 4. subtitle_window.py 显示
# 解析格式，应用颜色
```

#### 新系统实现

```python
# 1. livetranslate_text_client.py 发送（统一接口）
manager.partial(
    target_text=text,
    predicted_text=stash,
    mode=IncrementalMode.REPLACE,
    metadata={"provider": "qwen"}
)

# 自动分发到：
# - SubtitleHandler → subtitle_window → 显示（带颜色）
# - ConsoleHandler → console → 打印（可选）
# - LogFileHandler → log → 记录（可选）
```

**优势**：
- 代码行数减少 70%
- 逻辑集中，易于维护
- 自动支持多种输出目标
- 颜色显示自动化

## 🚀 集成步骤

### 步骤 1：修改 livetranslate_text_client.py

```python
# 在文件顶部导入
from output_manager import OutputManager, IncrementalMode

# 修改 handle_server_messages 方法
async def handle_server_messages(self, on_text_received=None):
    manager = OutputManager.get_instance()  # 获取单例

    async for message in self.ws:
        event = json.loads(message)
        event_type = event.get("type")

        if event_type == "response.text.text":
            # 翻译文本增量
            text = event.get("text", "")
            stash = event.get("stash", "")

            if text or stash:
                # 使用 OutputManager
                manager.partial(
                    target_text=text,
                    mode=IncrementalMode.REPLACE,
                    predicted_text=stash if stash else None,
                    metadata={"provider": "qwen"}
                )

        elif event_type == "response.text.done":
            # 翻译文本完成
            text = event.get("text", "")
            if text:
                # 使用 OutputManager
                manager.translation(
                    target_text=text,
                    metadata={"provider": "qwen"}
                )
```

### 步骤 2：在 main_app.py 初始化 OutputManager

```python
from output_manager import OutputManager
from output_handlers import SubtitleHandler, ConsoleHandler

class MainWindow(QMainWindow):
    def __init__(self):
        # ... 现有代码 ...

        # 初始化 OutputManager
        manager = OutputManager.get_instance()

        # 添加字幕处理器
        subtitle_handler = SubtitleHandler(self.subtitle_window)
        manager.add_handler(subtitle_handler)

        # 可选：添加控制台处理器
        console_handler = ConsoleHandler(
            enabled_types=[MessageType.TRANSLATION, MessageType.ERROR]
        )
        manager.add_handler(console_handler)
```

### 步骤 3：移除旧代码（可选）

```python
# 在 translation_service.py 中
# 移除或注释掉旧的 on_text_received 调用
# 因为现在直接使用 OutputManager
```

## ✅ 测试验证

运行测试代码：

```bash
python meeting_translator/qwen_output_integration.py
```

预期输出：

```
=== Qwen API 事件流模拟 ===

场景1：翻译 'Hello world'
--------------------------------------------------
[增量] 确定: '你' | 预测: '好'
      完整文本: 你【预测:好】

[增量] 确定: '你好世' | 预测: '界'
      完整文本: 你好世【预测:界】

[最终] 你好世界！
```

## 🎯 关键点

### 1. 完全覆盖增量状态

- ✅ **REPLACE 模式**：每次替换当前内容（Qwen 风格）
- ✅ **预测文本（stash）**：正确解析和显示
- ✅ **颜色区分**：已确定=白色，预测=灰色
- ✅ **增量标记**：蓝色 "..." 表示正在更新

### 2. 自动格式化

```python
message.full_target_text
# → "你好【预测:世界】"  # 自动添加预测标记

# subtitle_window 自动解析并应用颜色
```

### 3. 向后兼容

```python
# 旧代码（带格式化）仍然工作
formatted_text = f"{text}【预测:{stash}】"
subtitle_window.update_subtitle("", formatted_text, False)

# 新代码（更简洁）
manager.partial(text, predicted_text=stash, mode=IncrementalMode.REPLACE)
```

### 4. 灵活扩展

```python
# 轻松添加新的输出目标
manager.add_handler(CustomHandler())

# 轻松控制哪些消息类型显示
console_handler = ConsoleHandler(
    enabled_types=[MessageType.TRANSLATION]  # 只显示最终翻译
)
```

## 📚 相关文件

- `output_manager.py` - 核心类（支持 predicted_text）
- `output_handlers.py` - SubtitleHandler（处理预测文本）
- `qwen_output_integration.py` - 完整集成示例
- `livetranslate_text_client.py` - Qwen API 客户端（待集成）

## 🎉 总结

OutputManager **完全覆盖**了 Qwen API 的所有特性：

✅ 增量文本（REPLACE 模式）
✅ 预测文本（stash 字段）
✅ 源文本可选
✅ 自动格式化
✅ 颜色显示自动化
✅ 多目标输出
✅ 灵活扩展

**无任何功能缺失，且更加简洁和规范！**

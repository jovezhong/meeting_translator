# 统一输出管理器 (OutputManager)

## 📋 概述

统一输出管理器用于规范化会议翻译应用的所有输出，包括：
- **字幕窗口** (Subtitle Window)
- **控制台输出** (Console)
- **日志文件** (Log Files)

## 🎯 核心特性

### 1. 源文本可选
- ✅ 支持有源文本的翻译：`manager.translation("你好", source_text="Hello")`
- ✅ 支持无源文本的翻译：`manager.translation("你好")`
- ✅ 适用于OpenAI、Qwen、Doubao等不同API

### 2. 增量文本支持
- ✅ **APPEND模式**：增量追加到末尾
- ✅ **REPLACE模式**：增量替换当前内容（Qwen API）
- ✅ 自动跟踪增量文本状态

### 3. 消息类型分级
- `SOURCE_TEXT` - 源语言文本识别
- `TRANSLATION` - 最终翻译结果
- `PARTIAL_APPEND` - 增量文本（追加）
- `PARTIAL_REPLACE` - 增量文本（替换）
- `STATUS` - 状态信息（连接、启动等）
- `ERROR` - 错误信息
- `WARNING` - 警告信息
- `DEBUG` - 调试信息

### 4. 灵活的Handler和Formatter
- **Handler**：决定消息发送到哪里
- **Formatter**：决定消息如何格式化
- 可以自由组合和扩展

## 📁 文件结构

```
meeting_translator/
├── output_manager.py          # 核心类：OutputManager, MessageType, TranslationMessage
├── output_handlers.py         # 输出处理器：SubtitleHandler, ConsoleHandler, LogFileHandler
├── output_formatters.py       # 格式化器：SubtitleFormatter, ConsoleFormatter, LogFormatter
└── output_manager_example.py  # 使用示例和迁移指南
```

## 🚀 快速开始

### 步骤1：初始化OutputManager

在 `main_app.py` 的 `__init__` 方法中：

```python
from output_manager import OutputManager
from output_handlers import SubtitleHandler, ConsoleHandler, LogFileHandler

class MainWindow(QMainWindow):
    def __init__(self):
        # ... 现有代码 ...

        # 初始化OutputManager（可选）
        self.output_manager = OutputManager.get_instance()

        # 添加字幕处理器
        subtitle_handler = SubtitleHandler(self.subtitle_window)
        self.output_manager.add_handler(subtitle_handler)

        # 添加控制台处理器
        console_handler = ConsoleHandler(
            enabled_types=[MessageType.TRANSLATION, MessageType.STATUS, MessageType.ERROR],
            show_source=True
        )
        self.output_manager.add_handler(console_handler)

        # 添加日志处理器
        log_handler = LogFileHandler(logger_name="meeting_translator")
        self.output_manager.add_handler(log_handler)
```

### 步骤2：使用OutputManager发送消息

```python
from output_manager import MessageType, IncrementalMode

class MainWindow(QMainWindow):
    def on_translation_received(self, source_text: str, target_text: str, is_final: bool = True):
        """翻译接收回调"""
        if is_final:
            # 最终翻译
            self.output_manager.translation(
                target_text=target_text,
                source_text=source_text,
                metadata={"provider": self.provider}
            )
        else:
            # 增量翻译（Qwen API）
            self.output_manager.partial(
                target_text=target_text,
                mode=IncrementalMode.REPLACE,
                source_text=source_text,
                metadata={"provider": self.provider}
            )

    def on_service_error(self, error_message: str):
        """错误处理"""
        self.output_manager.error(error_message)

    def on_status_update(self, status: str):
        """状态更新"""
        self.output_manager.status(status)
```

## 📖 使用示例

### 示例1：发送翻译结果

```python
manager = OutputManager.get_instance()

# 有源文本
manager.translation(
    target_text="你好世界",
    source_text="Hello world",
    metadata={"provider": "openai"}
)

# 无源文本（Doubao API）
manager.translation(
    target_text="你好世界",
    metadata={"provider": "doubao"}
)
```

### 示例2：处理增量文本（Qwen API）

```python
# Qwen使用REPLACE模式
manager.partial(
    target_text="你好",
    mode=IncrementalMode.REPLACE,
    metadata={"provider": "qwen"}
)

# 后续更新：替换之前的增量文本
manager.partial(
    target_text="你好世界",
    mode=IncrementalMode.REPLACE,
    metadata={"provider": "qwen"}
)

# 最终翻译
manager.translation(
    target_text="你好世界！",
    metadata={"provider": "qwen"}
)
```

### 示例3：发送状态和错误信息

```python
# 状态信息
manager.status("正在连接到翻译服务...")
manager.status("连接成功")

# 错误信息
manager.error("连接失败: 网络超时")

# 警告信息
manager.warning("API密钥即将过期")
```

## 🔄 渐进式迁移指南

### 阶段1：并行运行（新旧共存）

```python
def on_translation_received(self, source_text: str, target_text: str, is_final: bool = True):
    # 旧代码（保留）
    logger.info(f"翻译: {source_text} -> {target_text}")
    self.subtitle_window.update_subtitle(source_text, target_text, is_final)

    # 新代码（测试中）
    try:
        if is_final:
            self.output_manager.translation(
                target_text=target_text,
                source_text=source_text,
                metadata={"provider": self.provider}
            )
    except Exception as e:
        logger.error(f"OutputManager失败: {e}")
```

### 阶段2：切换到新系统

```python
def on_translation_received(self, source_text: str, target_text: str, is_final: bool = True):
    # 移除旧代码，使用新代码
    if is_final:
        self.output_manager.translation(
            target_text=target_text,
            source_text=source_text,
            metadata={"provider": self.provider}
        )
    else:
        self.output_manager.partial(
            target_text=target_text,
            mode=IncrementalMode.REPLACE,
            source_text=source_text,
            metadata={"provider": self.provider}
        )
```

### 阶段3：优化和清理

- 移除旧的logger调用
- 移除直接的subtitle_window.update_subtitle调用
- 统一使用OutputManager

## 🎨 自定义Handler

你可以创建自定义Handler来支持额外的输出目标：

```python
from output_manager import BaseHandler, TranslationMessage, MessageType

class DatabaseHandler(BaseHandler):
    """将翻译保存到数据库"""

    def __init__(self, db_connection):
        super().__init__(enabled_types=[MessageType.TRANSLATION])
        self.db = db_connection

    def emit(self, message: TranslationMessage):
        """保存到数据库"""
        self.db.execute(
            "INSERT INTO translations (source, target, provider) VALUES (?, ?, ?)",
            (message.source_text, message.target_text,
             message.metadata.get("provider"))
        )

# 使用自定义handler
manager = OutputManager.get_instance()
manager.add_handler(DatabaseHandler(db_connection))
```

## 🆚 新旧系统对比

### 旧系统（分散且不统一）

```python
# 字幕窗口
self.subtitle_window.update_subtitle(source_text, target_text, is_final)

# 控制台
logger.info(f"翻译: {source_text} -> {target_text}")

# 格式混乱
logger.info(f"[说模式翻译] {source_text} → {target_text}")
logger.info(f"翻译: {target_text}")
```

### 新系统（统一且规范）

```python
# 统一接口
self.output_manager.translation(
    target_text=target_text,
    source_text=source_text,
    metadata={"provider": self.provider}
)

# 自动分发到所有handlers
# - 字幕窗口：[HH:MM:SS] 目标文本
# - 控制台：[PROVIDER] 源文本 -> 目标文本
# - 日志文件：[TIMESTAMP] [PROVIDER] 源文本 -> 目标文本
```

## ✅ 优势总结

1. **统一接口** - 一个方法调用，自动分发到所有输出目标
2. **类型安全** - 使用MessageType枚举，避免字符串错误
3. **灵活性** - 通过Handler和Formatter自由组合
4. **可扩展** - 轻松添加新的输出目标
5. **渐进式** - 新旧系统可以共存，逐步迁移
6. **源文本可选** - 完美支持不同的API特性
7. **增量支持** - 内置APPEND和REPLACE模式

## 📚 相关文档

- `output_manager.py` - 核心类实现
- `output_handlers.py` - 输出处理器实现
- `output_formatters.py` - 格式化器实现
- `output_manager_example.py` - 完整使用示例

## 🧪 测试

运行测试代码：

```bash
# 测试核心类
python meeting_translator/output_manager.py

# 测试Handlers
python meeting_translator/output_handlers.py

# 测试Formatters
python meeting_translator/output_formatters.py

# 查看使用示例
python meeting_translator/output_manager_example.py
```

## 📝 待办事项

- [ ] 在main_app.py中集成OutputManager（可选）
- [ ] 逐步迁移现有代码到新系统
- [ ] 添加配置文件支持（控制哪些handler启用）
- [ ] 性能测试和优化
- [ ] 完善错误处理和日志

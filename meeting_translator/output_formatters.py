"""
输出格式化器
提供不同的格式化风格用于翻译消息
"""

from typing import Optional
from datetime import datetime
from output_manager import BaseFormatter, TranslationMessage, MessageType, IncrementalMode


class SubtitleFormatter(BaseFormatter):
    """
    字幕窗口格式化器
    格式: [HH:MM:SS] 目标文本
    """

    def format(self, message: TranslationMessage) -> str:
        """格式化为字幕样式"""
        if message.message_type == MessageType.TRANSLATION:
            # 最终翻译：带时间戳
            timestamp = message.timestamp.strftime("%H:%M:%S")
            return f"[{timestamp}] {message.target_text}"
        elif message.message_type in [MessageType.PARTIAL_REPLACE, MessageType.PARTIAL_APPEND]:
            # 增量文本：不加时间戳
            return message.target_text
        return ""


class ConsoleFormatter(BaseFormatter):
    """
    控制台格式化器
    格式: [PROVIDER] 源文本 -> 目标文本
    """

    def __init__(self, show_provider: bool = True, show_source: bool = True,
                 arrow_style: str = "→"):
        """
        初始化控制台格式化器

        Args:
            show_provider: 是否显示provider标识
            show_source: 是否显示源文本
            arrow_style: 箭头样式
        """
        self.show_provider = show_provider
        self.show_source = show_source
        self.arrow_style = arrow_style

    def format(self, message: TranslationMessage) -> str:
        """格式化为控制台样式"""
        parts = []

        # 添加provider标识
        if self.show_provider:
            provider = message.metadata.get("provider", "").upper()
            if provider:
                parts.append(f"[{provider}]")

        # 添加源文本和箭头
        if self.show_source and message.source_text:
            parts.append(f"{message.source_text}")
            parts.append(self.arrow_style)

        # 添加目标文本
        parts.append(message.target_text)

        # 添加增量标记
        if not message.is_final:
            mode_mark = "..." if message.incremental_mode == IncrementalMode.REPLACE else "+"
            parts.append(f"({mode_mark})")

        return " ".join(parts)


class LogFormatter(BaseFormatter):
    """
    日志文件格式化器
    格式: [PROVIDER] 源文本 -> 目标文本 (元数据)
    """

    def __init__(self, include_metadata: bool = False,
                 timestamp_format: str = "%H:%M:%S"):
        """
        初始化日志格式化器

        Args:
            include_metadata: 是否包含元数据
            timestamp_format: 时间戳格式
        """
        self.include_metadata = include_metadata
        self.timestamp_format = timestamp_format

    def format(self, message: TranslationMessage) -> str:
        """格式化为日志样式"""
        parts = []

        # 添加时间戳
        timestamp = message.timestamp.strftime(self.timestamp_format)
        parts.append(f"[{timestamp}]")

        # 添加provider标识
        provider = message.metadata.get("provider", "")
        if provider:
            parts.append(f"[{provider.upper()}]")

        # 添加消息类型标记
        if message.message_type == MessageType.STATUS:
            parts.append("[状态]")
        elif message.message_type == MessageType.ERROR:
            parts.append("[错误]")
        elif message.message_type == MessageType.WARNING:
            parts.append("[警告]")
        elif not message.is_final:
            parts.append("[增量]")

        # 添加源文本
        if message.source_text:
            parts.append(f"{message.source_text} ->")

        # 添加目标文本
        parts.append(message.target_text)

        # 添加元数据
        if self.include_metadata and message.metadata:
            metadata_str = ", ".join(f"{k}={v}" for k, v in message.metadata.items())
            parts.append(f"({metadata_str})")

        return " ".join(parts)


class MinimalFormatter(BaseFormatter):
    """
    极简格式化器
    只输出目标文本，无任何装饰
    """

    def format(self, message: TranslationMessage) -> str:
        """极简格式"""
        return message.target_text


class DetailedFormatter(BaseFormatter):
    """
    详细格式化器
    包含所有信息：时间戳、provider、源文本、目标文本、元数据
    """

    def format(self, message: TranslationMessage) -> str:
        """详细格式"""
        lines = []

        # 第一行：时间戳和provider
        timestamp = message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        provider = message.metadata.get("provider", "unknown").upper()
        lines.append(f"[{timestamp}] [{provider}]")

        # 第二行：消息类型
        type_map = {
            MessageType.TRANSLATION: "翻译",
            MessageType.PARTIAL_REPLACE: "增量(替换)",
            MessageType.PARTIAL_APPEND: "增量(追加)",
            MessageType.STATUS: "状态",
            MessageType.ERROR: "错误",
            MessageType.WARNING: "警告",
        }
        type_label = type_map.get(message.message_type, message.message_type.value)
        lines.append(f"类型: {type_label}")

        # 第三行：源文本
        if message.source_text:
            lines.append(f"源文本: {message.source_text}")

        # 第四行：目标文本
        lines.append(f"目标文本: {message.target_text}")

        # 第五行：元数据
        if message.metadata:
            metadata_lines = [f"  {k}: {v}" for k, v in message.metadata.items()]
            lines.append("元数据:\n" + "\n".join(metadata_lines))

        return "\n".join(lines)


# 工厂函数
def create_formatter(formatter_type: str, **kwargs) -> BaseFormatter:
    """
    创建格式化器的工厂函数

    Args:
        formatter_type: 格式化器类型 (subtitle/console/log/minimal/detailed)
        **kwargs: 格式化器参数

    Returns:
        格式化器实例
    """
    formatters = {
        "subtitle": SubtitleFormatter,
        "console": ConsoleFormatter,
        "log": LogFormatter,
        "minimal": MinimalFormatter,
        "detailed": DetailedFormatter,
    }

    formatter_class = formatters.get(formatter_type.lower())
    if not formatter_class:
        raise ValueError(f"Unknown formatter type: {formatter_type}")

    return formatter_class(**kwargs)


# 测试代码
if __name__ == "__main__":
    from output_manager import TranslationMessage, MessageType, IncrementalMode

    # 创建测试消息
    message = TranslationMessage(
        message_type=MessageType.TRANSLATION,
        target_text="你好世界",
        source_text="Hello world",
        is_final=True,
        metadata={"provider": "openai", "confidence": 0.95}
    )

    # 测试不同格式化器
    print("=== 测试格式化器 ===\n")

    print("1. SubtitleFormatter:")
    print(SubtitleFormatter().format(message))
    print()

    print("2. ConsoleFormatter:")
    print(ConsoleFormatter().format(message))
    print()

    print("3. LogFormatter:")
    print(LogFormatter().format(message))
    print()

    print("4. MinimalFormatter:")
    print(MinimalFormatter().format(message))
    print()

    print("5. DetailedFormatter:")
    print(DetailedFormatter().format(message))
    print()

    # 测试增量消息
    partial_msg = TranslationMessage(
        message_type=MessageType.PARTIAL_REPLACE,
        target_text="你好",
        is_final=False,
        metadata={"provider": "qwen"}
    )

    print("6. ConsoleFormatter (Partial):")
    print(ConsoleFormatter().format(partial_msg))

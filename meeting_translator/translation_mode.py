# -*- coding: utf-8 -*-
"""
翻译模式定义与配置
"""
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class TranslationMode(Enum):
    """翻译模式"""
    LISTEN = "listen"          # 听：会议音频→中文字幕
    SPEAK = "speak"            # 说：中文麦克风→英文虚拟麦克风
    BIDIRECTIONAL = "both"     # 双向：同时运行听+说


@dataclass
class ModeConfig:
    """翻译模式配置"""
    mode: TranslationMode
    source_language: str
    target_language: str
    audio_enabled: bool        # 是否输出音频（说模式需要）
    voice: Optional[str] = "Cherry"  # 语音选择

    @staticmethod
    def for_listen():
        """
        听模式配置：英文→中文（仅字幕）

        Returns:
            ModeConfig: 听模式配置
        """
        return ModeConfig(
            mode=TranslationMode.LISTEN,
            source_language="en",
            target_language="zh",
            audio_enabled=False,
            voice=None
        )

    @staticmethod
    def for_speak():
        """
        说模式配置：中文→英文（音频输出）

        Returns:
            ModeConfig: 说模式配置
        """
        return ModeConfig(
            mode=TranslationMode.SPEAK,
            source_language="zh",
            target_language="en",
            audio_enabled=True,
            voice="Cherry"
        )

    @staticmethod
    def for_bidirectional():
        """
        双向模式配置：返回两个配置（听+说）

        Returns:
            tuple[ModeConfig, ModeConfig]: (听模式配置, 说模式配置)
        """
        return (ModeConfig.for_listen(), ModeConfig.for_speak())

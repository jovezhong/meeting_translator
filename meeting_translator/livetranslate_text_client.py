"""
阿里云 LiveTranslate 纯文本客户端
专门用于语音输入 → 文本翻译（听模式）
不包含音频输出功能，避免与语音客户端冲突
"""
import os
import time
import base64
import asyncio
import json
import websockets
import logging
try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio
import traceback

# 导入词汇表相关函数
from livetranslate_client import load_glossary, build_translation_instructions

# 导入 OutputManager
from output_manager import OutputManager, IncrementalMode

logger = logging.getLogger(__name__)


class LiveTranslateTextClient:
    """阿里云实时翻译客户端（纯文本模式）"""

    def __init__(
        self,
        api_key: str,
        source_language: str = "en",
        target_language: str = "zh",
        glossary_file: str = None
    ):
        """
        初始化翻译客户端（纯文本模式）

        Args:
            api_key: 阿里云 API Key
            source_language: 源语言 (en/zh/ja/ko/...)
            target_language: 目标语言 (zh/en/ja/ko/...)
            glossary_file: 词汇表文件路径（可选）
        """
        if not api_key:
            raise ValueError("API key cannot be empty.")

        self.api_key = api_key
        self.source_language = source_language
        self.target_language = target_language
        self.ws = None
        self.api_url = "wss://dashscope.aliyuncs.com/api-ws/v1/realtime?model=qwen3-livetranslate-flash-realtime"

        # 加载词汇表
        self.glossary = load_glossary(glossary_file)
        # 使用 OutputManager 记录状态信息（会写入日志文件，不在控制台显示）
        manager = OutputManager.get_instance()
        manager.debug(f"已加载词汇表，包含 {len(self.glossary)} 个术语")

        # 输入配置
        self.input_rate = 16000
        self.input_chunk = 1600
        self.input_format = pyaudio.paInt16
        self.input_channels = 1

        # 状态管理
        self.is_connected = False

    async def connect(self):
        """建立 WebSocket 连接"""
        headers = {"Authorization": f"Bearer {self.api_key}"}
        try:
            self.ws = await websockets.connect(
                self.api_url,
                extra_headers=headers
            )
            self.is_connected = True
            # 使用 OutputManager 记录状态信息
            manager = OutputManager.get_instance()
            manager.status(f"已连接到: {self.api_url}")
            await self.configure_session()
        except Exception as e:
            # 错误信息通过 OutputManager
            manager = OutputManager.get_instance()
            manager.error(f"连接失败: {e}")
            self.is_connected = False
            raise

    async def configure_session(self):
        """配置翻译会话（纯文本模式）"""
        config = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "session.update",
            "session": {
                "modalities": ["text"],  # 仅文本，不包含音频
                "input_audio_format": "pcm16",
                # 暂时移除 corpus.text，仅使用 instructions
                # "input_audio_transcription": {
                #     "language": self.source_language,
                #     "corpus": {
                #         "text": build_corpus_text(self.glossary)
                #     }
                # },
                "translation": {
                    "language": self.target_language
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 800
                }
            }
        }
        # 使用 OutputManager 记录状态信息
        manager = OutputManager.get_instance()
        manager.status("Session 配置完成（纯文本模式）")
        await self.ws.send(json.dumps(config))

    async def send_audio_chunk(self, audio_data: bytes):
        """发送音频数据块"""
        if not self.is_connected:
            return

        event = {
            "event_id": f"event_{int(time.time() * 1000)}",
            "type": "input_audio_buffer.append",
            "audio": base64.b64encode(audio_data).decode()
        }
        await self.ws.send(json.dumps(event))

    async def handle_server_messages(self, on_text_received=None):
        """处理服务器消息（纯文本模式）"""
        # 获取 OutputManager 单例
        manager = OutputManager.get_instance()

        try:
            async for message in self.ws:
                event = json.loads(message)
                event_type = event.get("type")

                if event_type == "response.done":
                    # 响应完成
                    # Token 用量信息使用 debug 级别（默认不显示）
                    usage = event.get("response", {}).get("usage", {})
                    if usage:
                        manager.debug(f"Token 使用: {json.dumps(usage)}")

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # 源语言转录完成
                    text = event.get("transcript", "")
                    language = event.get("language", "")
                    if text:
                        # 使用 OutputManager 记录源语言识别
                        manager.debug(f"[源语言] {text} (语言: {language})")
                        # 保留旧回调用于向后兼容
                        if on_text_received:
                            on_text_received(f"[源] {text}")

                elif event_type == "response.text.text":
                    # 翻译文本增量（纯文本模式特有）
                    # 提取 text（已确定）和 stash（未确定）
                    text = event.get("text", "")
                    stash = event.get("stash", "")

                    if text or stash:
                        # 使用 OutputManager 发送增量翻译
                        manager.partial(
                            target_text=text,
                            mode=IncrementalMode.REPLACE,
                            predicted_text=stash if stash else None,
                            metadata={"provider": "qwen"}
                        )

                elif event_type == "response.text.done":
                    # 翻译文本完成（纯文本模式特有）
                    text = event.get("text", "")
                    if text:
                        # 使用 OutputManager 发送最终翻译
                        manager.translation(
                            target_text=text,
                            metadata={"provider": "qwen", "mode": "LISTEN"}  # 标记为听模式
                        )

                        # 保留旧回调用于向后兼容（可选）
                        if on_text_received:
                            on_text_received(f"[译] {text}")

                elif event_type == "error":
                    error = event.get("error", {})
                    error_code = error.get("code", "Unknown")
                    error_msg = error.get("message", "Unknown error")

                    # 使用 OutputManager 发送错误信息（显示给用户）
                    manager.error(f"{error_code}: {error_msg}")

                    # InternalError 通常表示会话失效，需要重连
                    if error_code == "InternalError":
                        manager.warning("检测到 InternalError，连接可能已失效")
                        self.is_connected = False
                        break  # 退出消息循环，让上层重连

        except websockets.exceptions.ConnectionClosed as e:
            manager.warning(f"连接已关闭: {e}")
            self.is_connected = False
        except Exception as e:
            manager.error(f"消息处理错误: {e}")
            traceback.print_exc()
            self.is_connected = False

    async def start_microphone_streaming(self):
        """启动麦克风流式传输"""
        # 这个方法与 LiveTranslateClient 相同
        # 为了简洁，这里省略实现，需要时可以从父类复制
        pass

    async def close(self):
        """优雅地关闭连接"""
        self.is_connected = False

        if self.ws:
            try:
                await asyncio.wait_for(self.ws.close(), timeout=2.0)
                manager = OutputManager.get_instance()
                manager.debug("WebSocket 已关闭")
            except asyncio.TimeoutError:
                manager = OutputManager.get_instance()
                manager.debug("WebSocket 关闭超时")
            except Exception as e:
                manager = OutputManager.get_instance()
                manager.debug(f"关闭 WebSocket 时出错: {e}")

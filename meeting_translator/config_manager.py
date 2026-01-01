"""
配置管理器
保存和加载用户配置（模式、设备选择等）
"""
import json
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ConfigManager:
    """配置管理器"""

    def __init__(self, config_file: Optional[str] = None):
        """
        初始化配置管理器

        Args:
            config_file: 配置文件路径，默认为用户文档目录
        """
        if config_file is None:
            config_dir = os.path.join(os.path.expanduser("~"), "Documents", "会议翻译配置")
            os.makedirs(config_dir, exist_ok=True)
            config_file = os.path.join(config_dir, "config.json")

        self.config_file = config_file
        self.config: Dict[str, Any] = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            logger.info(f"配置文件不存在: {self.config_file}")
            logger.info("使用默认配置")
            return self._get_default_config()

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            logger.info(f"已从文件加载配置: {self.config_file}")
            return config
        except Exception as e:
            logger.error(f"加载配置文件失败: {e}")
            logger.info("使用默认配置")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "mode": "LISTEN",  # LISTEN / SPEAK / BIDIRECTIONAL
            "listen_device_name": None,
            "speak_input_device_name": None,
            "speak_output_device_name": None,
            "voice": "Cherry"  # Cherry / Nofish
        }

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            logger.info(f"配置已保存: {self.config_file}")
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value

    def get_mode(self) -> str:
        """获取翻译模式"""
        return self.config.get("mode", "LISTEN")

    def set_mode(self, mode: str):
        """设置翻译模式"""
        self.config["mode"] = mode
        self.save_config()

    def get_listen_device_name(self) -> Optional[str]:
        """获取听模式设备名"""
        return self.config.get("listen_device_name")

    def set_listen_device_name(self, name: Optional[str]):
        """设置听模式设备名"""
        self.config["listen_device_name"] = name
        self.save_config()

    def get_speak_input_device_name(self) -> Optional[str]:
        """获取说模式输入设备名"""
        return self.config.get("speak_input_device_name")

    def set_speak_input_device_name(self, name: Optional[str]):
        """设置说模式输入设备名"""
        self.config["speak_input_device_name"] = name
        self.save_config()

    def get_speak_output_device_name(self) -> Optional[str]:
        """获取说模式输出设备名"""
        return self.config.get("speak_output_device_name")

    def set_speak_output_device_name(self, name: Optional[str]):
        """设置说模式输出设备名"""
        self.config["speak_output_device_name"] = name
        self.save_config()

    def get_voice(self) -> str:
        """获取语音音色"""
        return self.config.get("voice", "Cherry")

    def set_voice(self, voice: str):
        """设置语音音色"""
        self.config["voice"] = voice
        self.save_config()


# 测试代码
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # 创建配置管理器
    config = ConfigManager()

    # 测试设置和获取
    print(f"当前模式: {config.get_mode()}")

    config.set_mode("SPEAK")
    config.set_listen_device_name("立体声混音")
    config.set_speak_input_device_name("麦克风")
    config.set_speak_output_device_name("VoiceMeeter Input")
    config.set_voice("Nofish")

    print(f"保存后的模式: {config.get_mode()}")
    print(f"听模式设备: {config.get_listen_device_name()}")
    print(f"说模式输入: {config.get_speak_input_device_name()}")
    print(f"说模式输出: {config.get_speak_output_device_name()}")
    print(f"语音音色: {config.get_voice()}")

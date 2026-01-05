"""
应用路径配置
统一管理所有数据目录的路径
"""

import os
from pathlib import Path


# ========== 根目录 ==========
# 所有应用数据统一放在 meeting_translator 目录下
MEETING_TRANSLATOR_ROOT = Path.home() / "Documents" / "meeting_translator"


# ========== 子目录 ==========
LOGS_DIR = MEETING_TRANSLATOR_ROOT / "logs"           # 日志文件
CONFIG_DIR = MEETING_TRANSLATOR_ROOT / "config"       # 配置文件
RECORDS_DIR = MEETING_TRANSLATOR_ROOT / "records"     # 会议记录（字幕）


# ========== 旧路径（用于迁移） ==========
# 保留以便向后兼容和自动迁移旧文件
LEGACY_LOGS_DIR = Path.home() / "Documents" / "会议翻译日志"
LEGACY_CONFIG_DIR = Path.home() / "Documents" / "会议翻译配置"
LEGACY_RECORDS_DIR = Path.home() / "Documents" / "会议记录"


def ensure_directories():
    """
    确保所有必要的目录存在
    如果不存在则创建
    """
    MEETING_TRANSLATOR_ROOT.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(exist_ok=True)
    CONFIG_DIR.mkdir(exist_ok=True)
    RECORDS_DIR.mkdir(exist_ok=True)


def migrate_legacy_files():
    """
    自动迁移旧目录中的文件到新目录

    Returns:
        dict: 迁移统计信息 {'logs': N, 'config': M, 'records': P}
    """
    stats = {'logs': 0, 'config': 0, 'records': 0}

    def migrate_files(src_dir, dst_dir, stat_key):
        """迁移单个目录的文件"""
        if not src_dir.exists():
            return 0

        dst_dir.mkdir(parents=True, exist_ok=True)
        count = 0

        for file in src_dir.iterdir():
            if file.is_file():
                dst_file = dst_dir / file.name
                # 只有目标文件不存在时才迁移（避免覆盖）
                if not dst_file.exists():
                    import shutil
                    try:
                        shutil.copy2(file, dst_file)
                        count += 1
                    except Exception as e:
                        print(f"[WARN] 迁移文件失败 {file}: {e}")

        return count

    stats['logs'] = migrate_files(LEGACY_LOGS_DIR, LOGS_DIR, 'logs')
    stats['config'] = migrate_files(LEGACY_CONFIG_DIR, CONFIG_DIR, 'config')
    stats['records'] = migrate_files(LEGACY_RECORDS_DIR, RECORDS_DIR, 'records')

    return stats


def get_initialization_message():
    """
    获取初始化信息（用于首次启动时的提示）

    Returns:
        str: 初始化信息或空字符串
    """
    messages = []

    # 检查是否是首次启动（新目录不存在）
    if not MEETING_TRANSLATOR_ROOT.exists():
        messages.append(f"✨ 创建数据目录: {MEETING_TRANSLATOR_ROOT}")

    # 检查是否有旧文件需要迁移
    has_legacy = any([
        LEGACY_LOGS_DIR.exists(),
        LEGACY_CONFIG_DIR.exists(),
        LEGACY_RECORDS_DIR.exists()
    ])

    if has_legacy:
        messages.append("📦 检测到旧版本数据，正在迁移...")
        stats = migrate_legacy_files()

        if sum(stats.values()) > 0:
            messages.append(f"✅ 迁移完成:")
            if stats['logs'] > 0:
                messages.append(f"   - 日志文件: {stats['logs']} 个")
            if stats['config'] > 0:
                messages.append(f"   - 配置文件: {stats['config']} 个")
            if stats['records'] > 0:
                messages.append(f"   - 会议记录: {stats['records']} 个")
            messages.append(f"\n旧文件仍然保留在:")
            messages.append(f"- {LEGACY_LOGS_DIR}")
            messages.append(f"- {LEGACY_CONFIG_DIR}")
            messages.append(f"- {LEGACY_RECORDS_DIR}")
            messages.append(f"\n你可以手动删除这些旧目录。")

    return "\n".join(messages)

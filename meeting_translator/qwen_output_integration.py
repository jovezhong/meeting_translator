"""
Qwen API 与 OutputManager 集成示例
演示如何处理 Qwen API 的增量文本和预测文本（stash）
"""

from output_manager import OutputManager, MessageType, IncrementalMode
from output_handlers import SubtitleHandler, ConsoleHandler


def setup_qwen_output(subtitle_window):
    """
    为 Qwen API 设置 OutputManager

    Args:
        subtitle_window: 字幕窗口实例
    """
    manager = OutputManager.get_instance()

    # 1. 添加字幕处理器（支持预测文本的颜色显示）
    subtitle_handler = SubtitleHandler(subtitle_window)
    manager.add_handler(subtitle_handler)

    # 2. 添加控制台处理器（可选）
    console_handler = ConsoleHandler(
        enabled_types=[MessageType.TRANSLATION, MessageType.STATUS, MessageType.ERROR],
        show_source=False  # Qwen通常不提供源文本
    )
    manager.add_handler(console_handler)

    return manager


def qwen_api_integration_example():
    """
    Qwen API 完整集成示例

    Qwen API 特点：
    1. response.text.text 事件 - 增量翻译（包含 text 和 stash）
    2. response.text.done 事件 - 最终翻译
    3. stash 是预测部分，应该用灰色显示
    """

    # ========== 在 livetranslate_text_client.py 中 ==========

    """
    修改 handle_server_messages 方法来使用 OutputManager

    原始代码（第143-162行）：
    ------------------------
    elif event_type == "response.text.text":
        # 翻译文本增量
        text = event.get("text", "")
        stash = event.get("stash", "")

        if text or stash:
            # 构造带预测的格式：已确定文本【预测:预测文本】
            if stash:
                formatted_text = f"{text}【预测:{stash}】"
            else:
                formatted_text = text

            # 传递格式化文本用于字幕显示
            if on_text_received:
                on_text_received(f"[译增量] {formatted_text}")

    新代码（使用 OutputManager）：
    ------------------------
    elif event_type == "response.text.text":
        # 翻译文本增量
        text = event.get("text", "")
        stash = event.get("stash", "")

        if text or stash:
            # 使用 OutputManager 发送增量消息
            manager = OutputManager.get_instance()
            manager.partial(
                target_text=text,              # 已确定部分
                mode=IncrementalMode.REPLACE,  # Qwen 使用 REPLACE 模式
                predicted_text=stash,          # 预测部分（stash）
                metadata={"provider": "qwen"}
            )

    elif event_type == "response.text.done":
        # 翻译文本完成
        text = event.get("text", "")
        if text:
            manager = OutputManager.get_instance()
            manager.translation(
                target_text=text,
                metadata={"provider": "qwen"}
            )
    """


def qwen_event_simulation():
    """
    模拟 Qwen API 事件流
    演示增量文本和预测文本的处理
    """
    print("=== Qwen API 事件流模拟 ===\n")

    # 初始化 OutputManager（测试用）
    manager = OutputManager.get_instance()

    # 添加测试 handler
    class TestHandler:
        def handle(self, message):
            if message.message_type in [MessageType.PARTIAL_REPLACE, MessageType.PARTIAL_APPEND]:
                print(f"[增量] 确定: '{message.target_text}' | 预测: '{message.predicted_text or '(无)'}'")
                if message.has_predicted_text:
                    print(f"      显示效果: {message.target_text}{message.predicted_text} (预测部分浅色)")
            elif message.message_type == MessageType.TRANSLATION:
                print(f"[最终] {message.target_text}")
            print()

    # 模拟 handler
    test_handler = TestHandler()
    manager.add_handler(test_handler)

    # ========== 场景1：翻译 "Hello world" ==========

    print("场景1：翻译 'Hello world'")
    print("-" * 50)

    # 增量1: "你" (stash: "好")
    manager.partial(
        target_text="你",
        predicted_text="好",
        mode=IncrementalMode.REPLACE,
        metadata={"provider": "qwen"}
    )
    # Output: [增量] 确定: '你' | 预测: '好'
    #         完整文本: 你【预测:好】

    # 增量2: "你好世" (stash: "界")
    manager.partial(
        target_text="你好世",
        predicted_text="界",
        mode=IncrementalMode.REPLACE,
        metadata={"provider": "qwen"}
    )
    # Output: [增量] 确定: '你好世' | 预测: '界'
    #         完整文本: 你好世【预测:界】

    # 增量3: "你好世界" (stash: 无，预测完成)
    manager.partial(
        target_text="你好世界",
        predicted_text="",  # 无预测部分
        mode=IncrementalMode.REPLACE,
        metadata={"provider": "qwen"}
    )
    # Output: [增量] 确定: '你好世界' | 预测: '(无)'

    # 最终翻译
    manager.translation(
        target_text="你好世界！",
        metadata={"provider": "qwen"}
    )
    # Output: [最终] 你好世界！


def qwen_parsing_example():
    """
    演示如何从 Qwen API 事件中提取 text 和 stash
    """
    print("=== Qwen API 事件解析示例 ===\n")

    # 模拟 Qwen API 事件
    qwen_events = [
        # Event 1: 增量翻译（有预测）
        {
            "type": "response.text.text",
            "text": "你好",
            "stash": "世界"
        },
        # Event 2: 增量翻译（预测更新）
        {
            "type": "response.text.text",
            "text": "你好世界",
            "stash": ""
        },
        # Event 3: 最终翻译
        {
            "type": "response.text.done",
            "text": "你好世界！"
        }
    ]

    manager = OutputManager.get_instance()

    for event in qwen_events:
        event_type = event.get("type")

        if event_type == "response.text.text":
            # 提取 text（已确定）和 stash（预测）
            text = event.get("text", "")
            stash = event.get("stash", "")

            print(f"[事件] response.text.text")
            print(f"  确定: '{text}'")
            print(f"  预测: '{stash}'")

            # 使用 OutputManager 发送
            manager.partial(
                target_text=text,
                mode=IncrementalMode.REPLACE,
                predicted_text=stash if stash else None,  # 空字符串转为 None
                metadata={"provider": "qwen"}
            )
            print(f"  → 已发送到 OutputManager\n")

        elif event_type == "response.text.done":
            # 最终翻译
            text = event.get("text", "")

            print(f"[事件] response.text.done")
            print(f"  最终: '{text}'")

            # 使用 OutputManager 发送
            manager.translation(
                target_text=text,
                metadata={"provider": "qwen"}
            )
            print(f"  → 已发送到 OutputManager\n")


def subtitle_color_demonstration():
    """
    演示 subtitle_window 如何处理预测文本的颜色
    """
    print("=== 字幕窗口颜色显示说明 ===\n")

    print("Qwen API 输出:")
    print("  text = '你好'")
    print("  stash = '世界'")
    print()

    print("SubtitleHandler 处理:")
    print("  1. 接收 message.partial('你好', predicted_text='世界')")
    print("  2. message.full_target_text = '你好【预测:世界】'")
    print("  3. subtitle_window.update_subtitle(target_text='你好【预测:世界】', is_final=False)")
    print()

    print("SubtitleWindow 渲染（subtitle_window.py:149-164）:")
    print("  1. 解析格式: /^(.*?)【预测:(.*?)）$/")
    print("  2. 已确定部分: '你好' → 白色 rgba(255, 255, 255, 0.95)")
    print("  3. 预测部分: '世界' → 灰色 rgba(160, 160, 160, 0.85)")
    print("  4. 末尾添加: '...' → 蓝色 rgba(100, 150, 255, 0.8)")
    print()

    print("HTML 输出:")
    print('''
    <p style="color: rgba(255, 255, 255, 0.95); margin: 5px 0;">
        [HH:MM:SS] 你好<span style="color: rgba(160, 160, 160, 0.85);">世界</span> <span style="color: rgba(100, 150, 255, 0.8);">...</span>
    </p>
    ''')


if __name__ == "__main__":
    print("=== Qwen API + OutputManager 集成 ===\n")

    # 1. 事件流模拟
    qwen_event_simulation()

    # 2. 事件解析示例
    # qwen_parsing_example()

    # 3. 颜色显示说明
    # subtitle_color_demonstration()

    print("\n=== 总结 ===")
    print("OutputManager 完全支持 Qwen API 的特性：")
    print("✅ 增量文本（REPLACE 模式）")
    print("✅ 预测文本（stash 字段）")
    print("✅ 源文本可选（Qwen 通常不提供）")
    print("✅ 自动格式化为 '已确定【预测:...】' 格式")
    print("✅ SubtitleWindow 自动处理颜色显示")

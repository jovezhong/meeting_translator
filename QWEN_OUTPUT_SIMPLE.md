# Qwen API 与 OutputManager 集成（简洁版）

## ✅ 简洁的显示格式

已移除 "【预测:...】" 格式，采用**简洁的颜色区分**：

- **已确定文本 (text)**：深色 `rgba(255, 255, 255, 0.95)` - 白色
- **预测文本 (stash)**：浅色 `rgba(160, 160, 160, 0.85)` - 灰色
- **增量标记**：蓝色 `...` 表示正在更新

### 显示效果

```
[HH:MM:SS] 你好(白色)世界(灰色) ...
           ↑已确定   ↑预测    ↑增量中
```

## 🎯 核心改进

### 1. TranslationMessage 扩展

```python
@dataclass
class TranslationMessage:
    target_text: str                       # 已确定部分 (text)
    predicted_text: Optional[str] = None   # 预测部分 (stash)

    @property
    def has_predicted_text(self) -> bool:
        return bool(self.predicted_text)
```

### 2. SubtitleHandler 简化

```python
# 直接传递 text 和 stash，不需要拼接
self.subtitle_window.update_subtitle(
    source_text=message.source_text or "",
    target_text=message.target_text,        # text（已确定）
    is_final=False,
    predicted_text=message.predicted_text   # stash（预测）
)
```

### 3. SubtitleWindow 自动处理颜色

```python
def _render_subtitles(self):
    if self.current_predicted_text:
        # 有预测：已确定（深色）+ 预测（浅色）
        html = f'''
            [{timestamp}]
            {self._escape_html(self.current_partial_text)}(白色)
            <span style="color: rgba(160, 160, 160, 0.85);">
                {self._escape_html(self.current_predicted_text)}(灰色)
            </span>
            <span style="color: rgba(100, 150, 255, 0.8);">...</span>(蓝色)
        '''
```

## 🚀 使用方式

### 在 Qwen API 中使用

```python
# livetranslate_text_client.py
elif event_type == "response.text.text":
    text = event.get("text", "")        # 已确定
    stash = event.get("stash", "")      # 预测

    if text or stash:
        manager = OutputManager.get_instance()
        manager.partial(
            target_text=text,              # 直接传递
            predicted_text=stash if stash else None,  # 直接传递
            mode=IncrementalMode.REPLACE,
            metadata={"provider": "qwen"}
        )
```

### 数据流

```
Qwen API
  ↓
text="你好", stash="世界"
  ↓
manager.partial(text, predicted_text=stash)
  ↓
TranslationMessage(target_text="你好", predicted_text="世界")
  ↓
SubtitleHandler
  ↓
subtitle_window.update_subtitle(
    target_text="你好",
    predicted_text="世界"
)
  ↓
渲染: 你好(白色) + 世界(灰色) + ...(蓝色)
```

## 🎨 颜色对比

| 文本类型 | 颜色 | RGBA | 说明 |
|---------|------|------|------|
| **已确定 (text)** | 白色 | `rgba(255, 255, 255, 0.95)` | 确定的翻译 |
| **预测 (stash)** | 灰色 | `rgba(160, 160, 160, 0.85)` | AI 预测部分 |
| **增量标记** | 蓝色 | `rgba(100, 150, 255, 0.8)` | `...` 表示未 finalize |
| **历史记录** | 白色 | `rgba(255, 255, 255, 1.0)` | 已完成的句子 |

## 📊 示例

### 翻译 "Hello world"

```
# Event 1: text="你", stash="好"
显示: [HH:MM:SS] 你好 ...

# Event 2: text="你好世", stash="界"
显示: [HH:MM:SS] 你好世界 ...

# Event 3: text="你好世界", stash="" (无预测)
显示: [HH:MM:SS] 你好世界 ...

# Event 4: 最终翻译 text="你好世界！"
显示: [HH:MM:SS] 你好世界！(历史记录，白色)
```

## ✅ 优势

1. **简洁** - 无需 "【预测:】" 等标记
2. **直观** - 颜色清晰区分确定/预测
3. **兼容** - 与现有 Qwen API 格式完全兼容
4. **灵活** - 易于调整颜色和样式

## 📝 测试

```bash
python meeting_translator/qwen_output_integration.py
```

输出：
```
[增量] 确定: '你' | 预测: '好'
      显示效果: 你好 (预测部分浅色)

[增量] 确定: '你好世' | 预测: '界'
      显示效果: 你好世界 (预测部分浅色)

[最终] 你好世界！
```

## 🔧 相关文件

- `output_manager.py` - TranslationMessage (支持 predicted_text)
- `output_handlers.py` - SubtitleHandler (传递 predicted_text)
- `subtitle_window.py` - 渲染逻辑 (颜色区分)
- `qwen_output_integration.py` - 完整示例

## 🎉 总结

**简洁 + 直观 = 最佳用户体验**

- ✅ 移除了冗余的 "【预测:】" 标记
- ✅ 保留了颜色区分（白色 vs 灰色）
- ✅ 完全兼容 Qwen API 的 text/stash 结构
- ✅ 代码更简洁，易于维护

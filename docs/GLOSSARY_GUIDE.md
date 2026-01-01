# 词汇表功能使用说明

## 📝 功能说明

词汇表功能通过**双重优化**提高专有名词的识别和翻译准确度：

1. **识别优化** (`corpus.text`)：帮助语音识别正确识别专有名词
2. **翻译优化** (`instructions`)：确保翻译使用正确的术语对照

## 📁 词汇表文件

位置：`meeting_translator/glossary.json`

格式：
```json
{
  "description": "Translation glossary for meeting translator",
  "glossary": {
    "ABC科技": "ABC Tech",
    "张总": "Mr. Zhang",
    "李经理": "Ms. Li",
    "核心产品": "Core Product",
    "业务系统": "Business System"
  }
}
```

## 🔧 如何修改词汇表

### 方法 1：直接编辑 JSON 文件

编辑 `meeting_translator/glossary.json`，添加或修改条目：

```json
{
  "glossary": {
    "新术语": "New Term",
    "另一个术语": "Another Term"
  }
}
```

**注意事项：**
- 左侧是中文术语，右侧是英文翻译
- 确保 JSON 格式正确（注意逗号、引号）
- 修改后重新启动程序生效

### 方法 2：使用 GlossaryManager（编程方式）

```python
from glossary_manager import GlossaryManager

# 创建管理器
manager = GlossaryManager()

# 添加术语
manager.add_term("新术语", "New Term")

# 删除术语
manager.remove_term("旧术语")

# 保存（自动）
```

## 🎯 最佳实践

### 1. 添加术语的原则

✅ **应该添加：**
- 公司名称：ABC科技 → ABC Tech
- 人名：张总 → Mr. Zhang
- 专业术语：业务系统 → Business System
- 产品名称：核心产品 → Core Product
- 项目名称、技术术语等

❌ **不需要添加：**
- 通用词汇（如"开发"、"系统"等）
- API 能正确翻译的常见词

### 2. 术语格式建议

**人名翻译：**
```json
"张总": "Mr. Zhang",
"李经理": "Ms. Li"
```
- 加上称谓（Mr./Ms.）
- 使用拼音或惯用译名

**公司名称：**
```json
"ABC科技": "ABC Tech"
```
- 使用官方英文名
- 保持大小写一致

**技术术语：**
```json
"业务系统": "Business System",
"数据平台": "Data Platform"
```
- 使用行业标准术语
- 保持简洁明了

### 3. 处理同音字

添加到 instructions 的提示会告诉 LLM 输入可能有同音字错误。

例如：
```
输入识别："ABC可计"（同音字错误）
实际应该："ABC科技"
翻译输出："ABC Tech"（✅ 仍然正确）
```

LLM 会根据上下文和词汇表自动纠正。

## 🚀 工作原理

### 识别阶段（corpus.text）

```python
context = """
会议背景：科技公司产品讨论会

关键术语：
ABC科技, 张总, 核心产品, 业务系统

示例：
ABC科技是ABC Tech。张总是Mr. Zhang。核心产品是Core Product。
"""
```

传入 `session.input_audio_transcription.corpus.text`，提高识别准确度。

### 翻译阶段（instructions）

```python
instructions = """
You are a professional translator for business meetings.

**CRITICAL TERMINOLOGY - MUST USE EXACT TRANSLATIONS:**
- ABC科技 → ABC Tech
- 张总 → Mr. Zhang
- 核心产品 → Core Product
- 业务系统 → Business System

**Translation Rules:**
0. 你的输入来自语音识别，有时候同音字可能被识别错误。
1. For the terms above, ALWAYS use the exact English translation specified.
2. Technical terms: Use the specified translations, NOT generic alternatives.
3. Maintain consistency throughout the conversation.
"""
```

传入 `session.instructions`，控制翻译输出。

## 📊 效果对比

### 无词汇表：
```
输入：我是张总，来自ABC科技。
翻译：I am Zhang from ABC Technology.
```

### 有词汇表：
```
输入：我是张总，来自ABC科技。
翻译：I am Mr. Zhang from ABC Tech.
     ✅ 正确的称谓    ✅ 正确的公司名
```

## 🔄 更新词汇表后

1. 编辑 `glossary.json`
2. **重启程序**（词汇表在启动时加载）
3. 测试新术语是否生效

## 💡 提示

- 词汇表不宜过长（建议 < 50 个术语）
- 只添加真正需要的专有名词
- 定期检查和更新术语表
- 测试确保翻译效果符合预期

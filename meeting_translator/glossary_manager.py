"""
术语表管理器
用于在翻译后进行专有名词替换
"""

import json
import os
import re
from typing import Dict, List, Tuple


class GlossaryManager:
    """术语表管理器"""

    def __init__(self, glossary_file: str = None):
        """
        Args:
            glossary_file: 术语表文件路径（JSON格式）
        """
        if glossary_file is None:
            config_dir = os.path.join(os.path.expanduser("~"), "Documents", "会议翻译配置")
            os.makedirs(config_dir, exist_ok=True)
            glossary_file = os.path.join(config_dir, "glossary.json")

        self.glossary_file = glossary_file
        self.glossary: Dict[str, str] = self._load_glossary()

        # 编译替换模式（提高效率）
        self._compile_patterns()

    def _load_glossary(self) -> Dict[str, str]:
        """加载术语表"""
        if os.path.exists(self.glossary_file):
            try:
                with open(self.glossary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("translations", {})
            except Exception as e:
                print(f"加载术语表失败: {e}")

        # 返回默认术语表
        return self._get_default_glossary()

    def _get_default_glossary(self) -> Dict[str, str]:
        """获取默认术语表"""
        return {
            # 公司名称示例
            "Example Company": "Example Company",
            "Sample Corp": "Sample Corporation",

            # 人名示例
            "Zhang Manager": "Mr. Zhang",
            "Li Manager": "Ms. Li",

            # 产品术语示例
            "core product": "Core Product",
            "business system": "Business System",
            "data platform": "Data Platform"
        }

    def _compile_patterns(self):
        """编译正则表达式模式（用于更智能的替换）"""
        self.patterns: List[Tuple[re.Pattern, str]] = []

        for wrong, correct in self.glossary.items():
            # 创建不区分大小写但保留边界的模式
            # 使用 \b 确保只匹配完整单词
            pattern = re.compile(r'\b' + re.escape(wrong) + r'\b', re.IGNORECASE)
            self.patterns.append((pattern, correct))

    def apply(self, text: str) -> str:
        """
        对文本应用术语替换

        Args:
            text: 原始翻译文本

        Returns:
            替换后的文本
        """
        result = text

        for pattern, replacement in self.patterns:
            result = pattern.sub(replacement, result)

        return result

    def save_glossary(self):
        """保存术语表到文件"""
        data = {
            "translations": self.glossary,
            "description": "Translation glossary for meeting translator"
        }

        try:
            with open(self.glossary_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存术语表失败: {e}")

    def add_term(self, wrong: str, correct: str):
        """
        添加术语

        Args:
            wrong: 错误的翻译
            correct: 正确的翻译
        """
        self.glossary[wrong] = correct
        self._compile_patterns()
        self.save_glossary()

    def remove_term(self, wrong: str):
        """删除术语"""
        if wrong in self.glossary:
            del self.glossary[wrong]
            self._compile_patterns()
            self.save_glossary()

    def get_context_for_corpus(self) -> str:
        """
        生成用于 corpus.text 的上下文

        基于术语表生成上下文文本，用于提高识别准确度
        """
        # 提取中文术语（从 correct 值中识别）
        chinese_terms = []
        english_terms = []

        for wrong, correct in self.glossary.items():
            # 假设包含中文字符的是中文术语
            if any('\u4e00' <= char <= '\u9fff' for char in correct):
                chinese_terms.append(correct)
            else:
                english_terms.append(correct)

        # 构建上下文
        context_parts = []

        if chinese_terms:
            context_parts.append("关键术语：\n" + "、".join(chinese_terms))

        if english_terms:
            context_parts.append("English terms:\n" + ", ".join(english_terms))

        # 添加翻译对照
        translation_pairs = [f"{wrong} → {correct}" for wrong, correct in self.glossary.items()]
        context_parts.append("翻译对照：\n" + "\n".join(translation_pairs))

        return "\n\n".join(context_parts)


# 使用示例
if __name__ == "__main__":
    manager = GlossaryManager()

    # 测试替换
    test_sentences = [
        "I am Zhai Hanbin from Yuxin Technology.",
        "Our credit system is very advanced.",
        "We offer online cash loan services.",
        "Ren Xiaoyao works at Yu Xin Technology."
    ]

    print("术语表替换测试:\n")
    print("=" * 80)

    for sentence in test_sentences:
        replaced = manager.apply(sentence)
        if sentence != replaced:
            print(f"原文: {sentence}")
            print(f"替换: {replaced}")
            print("-" * 80)
        else:
            print(f"无需替换: {sentence}")
            print("-" * 80)

    # 生成 corpus 上下文
    print("\n\n生成的 corpus.text 上下文:\n")
    print("=" * 80)
    print(manager.get_context_for_corpus())

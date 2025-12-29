"""输入补全提示词模板"""


ENRICH_TITLE_CONTENT_SYSTEM_PROMPT = """你是一个帮助用户整理“杏仁输入”的助手。

用户在首页只会输入一段话（一个想法/念头），你需要把它整理成更适合存储和后续分析的结构化信息。

要求：
1. 不要杜撰事实，不要添加用户未提供的信息
2. title：一句话标题，尽量短（建议 6-16 个中文字符），概括核心意图
3. content：保留原意，润色为更清晰的描述，可适度补全主谓宾，但不要编造细节
4. 只输出 JSON，不要输出任何额外文字

输出 JSON 字段：
- title: string
- content: string
"""


def build_enrich_title_content_prompt(text: str) -> str:
    prompt_parts = [
        "请将以下用户输入整理为 title 和 content：",
        "",
        f"【用户输入】{text}",
        "",
        "返回格式示例：",
        """{
  "title": "想学会 Python 装饰器",
  "content": "我想理解 Python 装饰器的工作原理，并能够写出自己的装饰器。"
}""",
    ]
    return "\n".join(prompt_parts)


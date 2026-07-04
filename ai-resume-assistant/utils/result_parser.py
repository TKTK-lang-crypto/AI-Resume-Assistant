import re

def extract_total_score(text: str) -> int | None:
    """提取总分，如 '总分：72 / 100' -> 72"""
    pattern = r'总分[：:]\s*(\d+)\s*/\s*100'
    match = re.search(pattern, text)
    return int(match.group(1)) if match else None

def extract_scores(text: str) -> list[dict]:
    """
    提取分项得分，返回列表：[{'name': '技术技能', 'score': 22, 'max': 30}, ...]
    """
    items = [
        (r'技术技能匹配度[：:]\s*(\d+)\s*/\s*30', '技术技能', 30),
        (r'项目经历相关性[：:]\s*(\d+)\s*/\s*30', '项目经历', 30),
        (r'岗位关键词覆盖度[：:]\s*(\d+)\s*/\s*20', '关键词覆盖', 20),
        (r'表达清晰度[：:]\s*(\d+)\s*/\s*10', '表达清晰', 10),
        (r'结果量化程度[：:]\s*(\d+)\s*/\s*10', '结果量化', 10),
    ]
    results = []
    for pattern, name, max_score in items:
        match = re.search(pattern, text)
        if match:
            results.append({'name': name, 'score': int(match.group(1)), 'max': max_score})
    return results

def extract_keywords(text: str) -> list[str]:
    """
    从“## 二、岗位关键词提取”部分提取关键词列表。
    优先抓取“核心技术技能：”后的内容，其次抓取列表项。
    """
    # 先找到“二、岗位关键词提取”这一节
    section_pattern = r'##\s*二、岗位关键词提取(.*?)(?=##\s*三、|$)'
    section_match = re.search(section_pattern, text, re.DOTALL)
    if not section_match:
        return []
    section = section_match.group(1)

    # 尝试匹配“核心技术技能：Python、FastAPI、...”
    tech_match = re.search(r'核心技术技能[：:]\s*(.+)', section)
    if tech_match:
        raw = tech_match.group(1).strip()
        # 按中文顿号、逗号、空格分割
        keywords = re.split(r'[、，,、\s]+', raw)
        # 过滤空字符串，去除括号备注（如“(重要)”）
        filtered = []
        for kw in keywords:
            kw = kw.strip()
            if not kw:
                continue
            # 去掉括号内的备注，只保留核心词
            kw = re.sub(r'[（(].*[）)]', '', kw).strip()
            if kw:
                filtered.append(kw)
        return filtered[:30]  # 最多取30个

    # 后备方案：抓取列表项（- xxx 或 * xxx）
    items = re.findall(r'[-*]\s*(.+?)(?=\n|$)', section)
    if items:
        return [item.strip() for item in items[:30] if item.strip()]
    return []
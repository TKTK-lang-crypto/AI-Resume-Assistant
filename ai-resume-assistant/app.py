import streamlit as st
from utils.llm_client import call_llm
from utils.prompt_templates import (
    build_keyword_prompt,
    build_match_score_prompt,
    build_gap_analysis_prompt,
    build_resume_optimization_prompt,
    build_interview_prompt,
    build_full_analysis_prompt,
)
from utils.file_parser import parse_resume_file
from utils.result_parser import extract_total_score, extract_scores, extract_keywords
import utils.db as db

# ---------- 页面配置 ----------
st.set_page_config(page_title="AI 简历优化助手", page_icon="📄", layout="wide")

# 初始化数据库
db.init_db()

# ---------- 初始化 session_state ----------
if "resume_text_area" not in st.session_state:
    st.session_state.resume_text_area = ""
if "job_description" not in st.session_state:
    st.session_state.job_description = ""

for key in ["keyword_result", "match_result", "gap_result", "optimization_result", "interview_result", "full_result"]:
    if key not in st.session_state:
        st.session_state[key] = ""

# ---------- 标题 ----------
st.title("📄 AI 简历优化助手")
st.caption("基于大模型的简历与岗位 JD 匹配分析工具")

# ---------- 侧边栏 ----------
with st.sidebar:
    st.header("功能说明")
    st.markdown(
        """
        **功能模块**：
        - 🔍 岗位关键词提取（可视化标签）
        - 📊 简历匹配度评分（进度条+指标卡）
        - 🧩 技能缺口分析
        - ✍️ 简历优化建议
        - 🎤 模拟面试题生成
        - 🚀 一键完整分析（仪表盘+完整报告）

        **支持文件格式**：PDF、DOCX、TXT
        """
    )
    st.divider()

    analysis_mode = st.selectbox(
        "选择分析模式",
        ["快速分析", "深度分析", "简历润色", "模拟面试"],
        key="analysis_mode_sidebar"
    )

    st.divider()
    st.markdown("### 开发进度")
    st.markdown(
        """
        ✅ 页面原型
        ✅ 接入大模型 API
        ✅ 拆分 Prompt 功能
        ✅ 文件上传支持
        ✅ 结果结构化展示
        ✅ 历史记录持久化
        """
    )
    st.divider()

    if st.button("🧹 清空所有结果", use_container_width=True, key="clear_all_btn"):
        for key in ["keyword_result", "match_result", "gap_result", "optimization_result", "interview_result", "full_result"]:
            st.session_state[key] = ""
        st.rerun()

    # ---------- 历史记录区域 ----------
    with st.expander("📜 历史记录", expanded=False):
        records = db.get_all_records(limit=20)
        if not records:
            st.info("暂无历史记录。")
        else:
            options = []
            id_map = {}
            for rec in records:
                type_map = {
                    'keyword': '关键词',
                    'match': '匹配度',
                    'gap': '缺口',
                    'optimize': '优化',
                    'interview': '面试题',
                    'full': '完整分析'
                }
                display = f"{type_map.get(rec['analysis_type'], rec['analysis_type'])} - {rec['created_at'][:16]}"
                options.append(display)
                id_map[display] = rec['id']

            selected_display = st.selectbox(
                "选择一条历史记录",
                options,
                key="history_select"
            )
            if selected_display:
                rec_id = id_map[selected_display]
                rec = next((r for r in records if r['id'] == rec_id), None)
                if rec:
                    st.text_area(
                        "结果预览",
                        rec['result'][:300] + "...",
                        height=100,
                        key="history_preview",
                        disabled=True
                    )
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("📂 加载到当前", key="load_history", use_container_width=True):
                            st.session_state.resume_text_area = rec['resume_text']
                            st.session_state.job_description = rec['job_description']
                            type_key_map = {
                                'keyword': 'keyword_result',
                                'match': 'match_result',
                                'gap': 'gap_result',
                                'optimize': 'optimization_result',
                                'interview': 'interview_result',
                                'full': 'full_result'
                            }
                            key = type_key_map.get(rec['analysis_type'])
                            if key:
                                st.session_state[key] = rec['result']
                            st.success("已加载历史记录！")
                            st.rerun()
                    with col2:
                        if st.button("🗑️ 删除", key="delete_history", use_container_width=True):
                            db.delete_record(rec_id)
                            st.success("已删除该记录。")
                            st.rerun()

            if st.button("🗑️ 清空所有历史记录", key="clear_history", use_container_width=True):
                db.clear_all_records()
                st.success("已清空所有历史记录。")
                st.rerun()

# ---------- 输入区域 ----------
st.subheader("1. 输入简历和岗位 JD")
col1, col2 = st.columns(2, gap="medium")

with col1:
    st.markdown("### 你的简历内容")
    uploaded_file = st.file_uploader(
        "上传简历文件（PDF / DOCX / TXT）",
        type=["pdf", "docx", "txt"],
        key="resume_uploader",
        help="上传后自动提取文本，将覆盖下方手动输入的内容。"
    )

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        file_type = uploaded_file.name.split(".")[-1].lower()
        try:
            parsed_text = parse_resume_file(file_bytes, file_type)
            if parsed_text.strip():
                st.session_state.resume_text_area = parsed_text
                st.success(f"✅ 解析成功！共提取 {len(parsed_text)} 个字符。")
                st.rerun()
            else:
                st.error("❌ 解析结果为空，可能是扫描件或图片型 PDF。请手动输入。")
        except Exception as e:
            st.error(f"❌ 文件解析失败：{str(e)}")

    st.text_area(
        label="或手动粘贴简历文本",
        height=300,
        placeholder="例如：教育背景、技能、项目经历、实习经历等...",
        key="resume_text_area"
    )

with col2:
    st.markdown("### 目标岗位 JD")
    job_description = st.text_area(
        label="请粘贴目标岗位描述",
        height=300,
        placeholder="例如：AI 应用开发实习生岗位要求、技能要求、加分项等...",
        key="jd_text_area"
    )
    # 同步到统一变量
    st.session_state.job_description = st.session_state.jd_text_area

# ---------- 功能按钮 ----------
st.subheader("2. 选择分析功能")

row1_cols = st.columns(3)
with row1_cols[0]:
    keyword_btn = st.button("🔍 提取岗位关键词", use_container_width=True, key="btn_keyword")
with row1_cols[1]:
    match_btn = st.button("📊 匹配度评分", use_container_width=True, key="btn_match")
with row1_cols[2]:
    gap_btn = st.button("🧩 技能缺口分析", use_container_width=True, key="btn_gap")

row2_cols = st.columns(3)
with row2_cols[0]:
    optimize_btn = st.button("✍️ 简历优化建议", use_container_width=True, key="btn_optimize")
with row2_cols[1]:
    interview_btn = st.button("🎤 模拟面试题", use_container_width=True, key="btn_interview")
with row2_cols[2]:
    full_btn = st.button("🚀 一键完整分析", type="primary", use_container_width=True, key="btn_full")

# ---------- 输入校验 & 通用调用 ----------
def check_inputs(require_resume=True):
    if require_resume and not st.session_state.get("resume_text_area", "").strip():
        st.warning("请先输入简历内容或上传简历文件。", icon="⚠️")
        return False
    if not st.session_state.job_description.strip():
        st.warning("请先输入目标岗位 JD。", icon="⚠️")
        return False
    return True

def safe_call_llm(prompt, result_key, analysis_type, success_msg="分析完成！"):
    try:
        with st.spinner("正在调用大模型，请稍候..."):
            result = call_llm(prompt)
        st.session_state[result_key] = result
        db.save_record(
            analysis_type=analysis_type,
            resume_text=st.session_state.resume_text_area,
            job_description=st.session_state.job_description,
            result=result
        )
        st.success(success_msg)
    except Exception as e:
        st.error(f"调用失败：{str(e)}")
        st.session_state[result_key] = ""

# ---------- 按钮逻辑 ----------
if keyword_btn:
    if check_inputs(require_resume=False):
        prompt = build_keyword_prompt(st.session_state.job_description)
        safe_call_llm(prompt, "keyword_result", "keyword", "关键词提取完成！")

if match_btn:
    if check_inputs(require_resume=True):
        prompt = build_match_score_prompt(
            st.session_state.resume_text_area,
            st.session_state.job_description
        )
        safe_call_llm(prompt, "match_result", "match", "匹配度评分完成！")

if gap_btn:
    if check_inputs(require_resume=True):
        prompt = build_gap_analysis_prompt(
            st.session_state.resume_text_area,
            st.session_state.job_description
        )
        safe_call_llm(prompt, "gap_result", "gap", "技能缺口分析完成！")

if optimize_btn:
    if check_inputs(require_resume=True):
        prompt = build_resume_optimization_prompt(
            st.session_state.resume_text_area,
            st.session_state.job_description
        )
        safe_call_llm(prompt, "optimization_result", "optimize", "简历优化建议生成完成！")

if interview_btn:
    if check_inputs(require_resume=True):
        prompt = build_interview_prompt(
            st.session_state.resume_text_area,
            st.session_state.job_description
        )
        safe_call_llm(prompt, "interview_result", "interview", "模拟面试题生成完成！")

if full_btn:
    if check_inputs(require_resume=True):
        prompt = build_full_analysis_prompt(
            st.session_state.resume_text_area,
            st.session_state.job_description,
            analysis_mode
        )
        safe_call_llm(prompt, "full_result", "full", "完整分析报告生成完成！")

# ---------- 辅助渲染函数 ----------
def render_keyword_tags(keywords: list[str]):
    if not keywords:
        return
    display_kws = keywords[:30]
    html = '<div style="display: flex; flex-wrap: wrap; gap: 8px; margin: 10px 0;">'
    for kw in display_kws:
        html += f'<span style="background-color: #e0f2fe; color: #0369a1; padding: 4px 14px; border-radius: 20px; font-weight: 500; font-size: 14px; border: 1px solid #bae6fd;">{kw}</span>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)
    st.caption(f"共提取 {len(display_kws)} 个关键词")

def render_match_dashboard(result: str):
    total = extract_total_score(result)
    scores = extract_scores(result)

    if total is not None:
        col1, col2 = st.columns([1, 3])
        with col1:
            st.metric(label="综合匹配度", value=f"{total}/100", delta=None)
        with col2:
            st.progress(total / 100, text=f"得分 {total}%")
        st.divider()

    if scores:
        cols = st.columns(len(scores))
        for i, item in enumerate(scores):
            with cols[i]:
                st.metric(
                    label=item['name'],
                    value=f"{item['score']}/{item['max']}",
                    delta=None
                )
        st.divider()

def display_result_with_fallback(result: str, mode: str):
    if not result:
        return

    if mode == "keyword":
        keywords = extract_keywords(result)
        if keywords:
            st.markdown("#### 🔥 岗位关键词标签")
            render_keyword_tags(keywords)
        else:
            st.markdown("#### 关键词提取结果（原始格式）")
            st.markdown(result)

    elif mode == "match":
        total = extract_total_score(result)
        scores = extract_scores(result)
        if total is not None or scores:
            render_match_dashboard(result)
        with st.expander("📄 查看详细评分说明"):
            st.markdown(result)

    elif mode == "full":
        total = extract_total_score(result)
        scores = extract_scores(result)
        keywords = extract_keywords(result)

        if total is not None or scores or keywords:
            st.markdown("#### 📊 分析概览")
            if total is not None:
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric(label="综合匹配度", value=f"{total}/100")
                with col2:
                    st.progress(total / 100)
                st.divider()

            if scores:
                cols = st.columns(len(scores))
                for i, item in enumerate(scores):
                    with cols[i]:
                        st.metric(label=item['name'], value=f"{item['score']}/{item['max']}")
                st.divider()

            if keywords:
                st.markdown("#### 🔥 岗位关键词")
                render_keyword_tags(keywords)
                st.divider()

        with st.expander("📄 查看完整分析报告（Markdown）"):
            st.markdown(result)

    else:
        st.markdown(result)

# ---------- 结果展示 ----------
st.subheader("3. 分析结果")
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["🔍 岗位关键词", "📊 匹配度", "🧩 技能缺口", "✍️ 简历优化", "🎤 面试题", "🚀 完整分析"]
)

with tab1:
    result = st.session_state.get("keyword_result", "")
    if result:
        display_result_with_fallback(result, "keyword")
        st.download_button(
            label="📥 下载关键词结果 (Markdown)",
            data=result,
            file_name="job_keywords.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_keyword_result"
        )
    else:
        st.info("点击「提取岗位关键词」生成结果。")

with tab2:
    result = st.session_state.get("match_result", "")
    if result:
        display_result_with_fallback(result, "match")
        st.download_button(
            label="📥 下载匹配度评分 (Markdown)",
            data=result,
            file_name="resume_match_score.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_match_result"
        )
    else:
        st.info("点击「匹配度评分」生成结果。")

with tab3:
    result = st.session_state.get("gap_result", "")
    if result:
        st.markdown(result)
        st.download_button(
            label="📥 下载技能缺口分析",
            data=result,
            file_name="skill_gap_analysis.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_gap_result"
        )
    else:
        st.info("点击「技能缺口分析」生成结果。")

with tab4:
    result = st.session_state.get("optimization_result", "")
    if result:
        st.markdown(result)
        st.download_button(
            label="📥 下载简历优化建议",
            data=result,
            file_name="resume_optimization.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_optimization_result"
        )
    else:
        st.info("点击「简历优化建议」生成结果。")

with tab5:
    result = st.session_state.get("interview_result", "")
    if result:
        st.markdown(result)
        st.download_button(
            label="📥 下载模拟面试题",
            data=result,
            file_name="interview_questions.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_interview_result"
        )
    else:
        st.info("点击「模拟面试题」生成结果。")

with tab6:
    result = st.session_state.get("full_result", "")
    if result:
        display_result_with_fallback(result, "full")
        st.download_button(
            label="📥 下载完整分析报告",
            data=result,
            file_name="full_resume_analysis.md",
            mime="text/markdown",
            use_container_width=True,
            key="download_full_result"
        )
    else:
        st.info("点击「一键完整分析」生成结果。")

st.divider()
st.caption("AI Resume Assistant v0.7 | 统一数据源，修复上传后分析问题")

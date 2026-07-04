import os
import streamlit as st
from openai import OpenAI


def get_config_value(key: str, default: str = "") -> str:
    """
    优先从 Streamlit secrets 读取配置；
    如果没有，再从环境变量读取。
    """
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass

    return os.getenv(key, default)


def get_llm_client() -> OpenAI:
    """
    创建 OpenAI-compatible 客户端。
    可用于 DeepSeek、OpenAI 或其他兼容服务。
    """
    api_key = get_config_value("API_KEY")
    base_url = get_config_value("BASE_URL", "https://api.deepseek.com")

    if not api_key:
        raise ValueError("未检测到 API_KEY，请先在 .streamlit/secrets.toml 中配置 API_KEY。")

    client = OpenAI(
        api_key=api_key,
        base_url=base_url
    )

    return client


def call_llm(prompt: str) -> str:
    """
    调用大模型并返回文本结果。
    """
    client = get_llm_client()
    model_name = get_config_value("MODEL_NAME", "deepseek-v4-flash")

    try:
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": "你是一名专业、严谨、诚实的技术招聘分析专家。"
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.3
        )

        return response.choices[0].message.content

    except Exception as e:
        raise RuntimeError(f"大模型调用失败：{str(e)}")
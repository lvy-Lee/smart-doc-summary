from dotenv import load_dotenv
import streamlit as st
from openai import OpenAI

from consts import PROVIDERS, BASE_PROMPT, MAX_TEXT_LENGTH, MAX_FILE_SIZE
from utils import (
    truncate_text,
    is_valid_url,
    read_file_content,
    fetch_url_content,
    get_zhipu_key,
    call_llm,
    call_llm_stream,
)

load_dotenv()

st.set_page_config(page_title="智能文档摘要工具", page_icon="📝")
st.title("📝 智能文档摘要工具")

if "summary" not in st.session_state:
    st.session_state.summary = None
if "summary_tab" not in st.session_state:
    st.session_state.summary_tab = None
if "history" not in st.session_state:
    st.session_state.history = []


def _add_to_history(summary, source):
    st.session_state.history.append({
        "source": source,
        "content": summary,
    })

def _show_summary(tab_name):
    if st.session_state.summary and st.session_state.summary_tab == tab_name:
        st.success("✅ 摘要生成成功！")
        st.markdown(st.session_state.summary)
        fmt = st.selectbox(
            "下载格式", [".md", ".txt"],
            key=f"fmt_{tab_name}",
            label_visibility="collapsed",
        )
        st.download_button(
            "📥 下载摘要",
            st.session_state.summary,
            file_name=f"summary{fmt}",
        )


with st.sidebar:
    st.header("使用说明")
    st.markdown(
        """
- **粘贴文本**、**上传文件**或**输入网址**
- AI 会自动识别文档类型，选用最合适的摘要结构
        """
    )
    st.markdown("---")

    with st.popover("⚙️ 模型配置"):
        st.caption("当前支持:智谱 / DeepSeek / Qwen / Doubao / Kimi / 讯飞星火")
        cfg_key = st.text_input("API Key（留空用默认）", type="password", key="cfg_key")

        if not cfg_key:
            cfg_provider = "智谱AI"
            cfg_model = "glm-4.7-flash"
            st.info("填写您的 API Key 即可选择对应的厂商和模型")
        else:
            cfg_provider = st.selectbox("选择厂商", list(PROVIDERS.keys()), key="cfg_provider")
            model_options = PROVIDERS[cfg_provider]["models"] + ["自定义"]
            cfg_model_choice = st.selectbox("选择模型", model_options, key="cfg_model_choice")
            if cfg_model_choice == "自定义":
                cfg_model = st.text_input("输入模型名称", placeholder="例如: glm-4.7-flash", key="cfg_model_custom")
            else:
                cfg_model = cfg_model_choice

    if cfg_key:
        api_key = cfg_key
        resolved_provider = cfg_provider
    else:
        api_key = get_zhipu_key()
        resolved_provider = "智谱AI"

    if not api_key:
        st.error("未配置 API Key")
        st.stop()

    pconf = PROVIDERS[resolved_provider]
    client = OpenAI(api_key=api_key, base_url=pconf["base_url"])
    st.caption(f"当前: {resolved_provider} · {cfg_model}")

tab1, tab2, tab3 = st.tabs(["📄 粘贴文本", "📁 上传文件", "🔗 输入网址"])

with tab1:
    user_input = st.text_area("把你要总结的文本粘贴到这里：", height=250)
    if user_input.strip():
        st.caption(f"字符数：{len(user_input)}　｜　估算 Token：{len(user_input) // 4}")
    if st.button("✨ 生成摘要") and user_input.strip():
        text = truncate_text(user_input)
        if len(user_input) > MAX_TEXT_LENGTH:
            st.warning(f"文本过长（{len(user_input)} 字符），已截断至前 {MAX_TEXT_LENGTH} 字符")
        with st.spinner("AI 正在阅读并总结..."):
            try:
                summary = st.write_stream(
                    call_llm_stream(client, text, BASE_PROMPT, cfg_model, pconf)
                )
                if summary:
                    st.session_state.summary = summary
                    st.session_state.summary_tab = "paste"
                    _add_to_history(summary, "粘贴文本")
            except Exception as e:
                st.error(f"API 调用失败：{e}")
    _show_summary("paste")

with tab2:
    uploaded_file = st.file_uploader("选择文件", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        if uploaded_file.size > MAX_FILE_SIZE:
            st.error("文件超过 50MB 限制，请选择较小的文件")
            st.stop()
        file_content = read_file_content(uploaded_file)
        if not file_content.strip():
            st.warning("该文件未包含可提取的文本内容（可能为扫描件）")
        else:
            with st.expander(f"📄 文件预览（{len(file_content)} 字符）", expanded=False):
                st.code(file_content[:2000], language="text")
            if st.button("✨ 摘要此文件"):
                with st.spinner("AI 正在阅读并总结..."):
                    try:
                        summary = st.write_stream(
                            call_llm_stream(client, file_content, BASE_PROMPT, cfg_model, pconf)
                        )
                        if summary:
                            st.session_state.summary = summary
                            st.session_state.summary_tab = "file"
                            _add_to_history(summary, f"文件 {uploaded_file.name}")
                    except Exception as e:
                        st.error(f"API 调用失败：{e}")
    _show_summary("file")

with tab3:
    url = st.text_input("输入网页链接：", placeholder="https://...")
    if st.button("✨ 摘要此网页") and url.strip():
        if not is_valid_url(url.strip()):
            st.error("请输入有效的网址（以 http:// 或 https:// 开头）")
            st.stop()
        with st.spinner("正在获取网页内容..."):
            try:
                page_content = fetch_url_content(url)
            except Exception as e:
                st.error(f"获取网页内容失败：{e}")
                st.stop()
        if page_content.strip():
            st.caption(f"已获取 {len(page_content)} 字符")
            with st.spinner("AI 正在阅读并总结..."):
                try:
                    summary = st.write_stream(
                        call_llm_stream(client, page_content, BASE_PROMPT, cfg_model, pconf)
                    )
                    if summary:
                        st.session_state.summary = summary
                        st.session_state.summary_tab = "url"
                        _add_to_history(summary, f"网页 {url[:50]}")
                except Exception as e:
                    st.error(f"API 调用失败：{e}")
    _show_summary("url")

if st.session_state.history:
    st.markdown("---")
    with st.expander(f"📜 历史记录（{len(st.session_state.history)} 条）", expanded=False):
        for i, h in enumerate(st.session_state.history):
            preview = h["content"][:80].replace("\n", " ")
            if st.button(f"{h['source']} — {preview}...", key=f"hist_{i}"):
                st.session_state.summary = h["content"]
                st.rerun()
        if st.button("🗑️ 清空历史", type="secondary"):
            st.session_state.history = []
            st.session_state.summary = None
            st.rerun()

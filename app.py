import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()
from openai import OpenAI

PROVIDERS = {
    "智谱AI": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "models": ["glm-4.7-flash", "glm-4-flash", "glm-z1-flash", "glm-4-plus"],
        "supports_thinking": True,
    },
    "DeepSeek": {
        "base_url": "https://api.deepseek.com",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "supports_thinking": True,
    },
    "阿里千问": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max", "qwen3-plus", "qwen3-235b-a100b"],
        "supports_thinking": False,
    },
    "字节豆包": {
        "base_url": "https://ark.cn-beijing.volces.com/api/v3/",
        "models": ["doubao-pro-32k", "doubao-lite-32k", "doubao-pro-128k"],
        "supports_thinking": False,
    },
    "Kimi": {
        "base_url": "https://api.moonshot.cn/v1",
        "models": ["moonshot-v1-8k", "moonshot-v1-32k", "moonshot-v1-128k"],
        "supports_thinking": False,
    },
    "讯飞星火": {
        "base_url": "https://spark-api-open.xf-yun.com/v1",
        "models": ["spark-lite", "spark-pro", "spark-ultra"],
        "supports_thinking": False,
    },
}

BASE_PROMPT = """你是一个专业的文档摘要助手。
首先判断输入文本的类型，然后选用最合适的结构输出。在摘要开头用图标标明类型。

【判断规则】
- 有情节、人物、对话 → 小说/叙事类
- 有功能、接口、需求描述 → 技术/需求文档类
- 有时间、发言、决议 → 会议/演讲类
- 有方法、数据、论证 → 论文/研究报告类
- 其他 → 通用格式

## 📖 小说/叙事类
【情节概要】故事背景与本章主线进展
【关键事件】重要情节转折或冲突
【伏笔悬念】未解之谜或埋下的线索

## 📄 技术/需求文档类
【需求背景】项目背景与目标
【核心要求】功能、性能、约束等关键需求
【待办事项】需跟进完成的任务

## 🗣 会议/演讲类
【议题背景】时间、主题、参会方
【核心观点/决议】主要发言内容与结论
【行动项】明确的待办任务及负责人

## 📊 论文/研究报告类
【研究问题】论文要解决什么问题
【方法与数据】采用的方法和数据集
【核心结论】主要发现和结论

## 通用格式
【概述】文档的核心主题
【要点】分点列出关键信息
【建议】结论或后续建议
"""

STYLE_INSTRUCTIONS = {
    "标准": "请按上述结构输出，每部分篇幅适中，覆盖核心信息。",
    "简要": "请按上述结构输出，但每部分限制为1-2句话，只保留最核心信息。不适用当前文档类型的【】可跳过。",
    "详细": "请按上述结构输出，尽可能详细，包含关键数据、引文和具体细节。如内容需要可适当扩展或增加子段。",
}


def get_zhipu_key():
    key = os.getenv("ZHIPUAI_API_KEY")
    if not key:
        try:
            key = st.secrets.get("ZHIPUAI_API_KEY")
        except Exception:
            pass
    return key


def read_file_content(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".txt"):
        try:
            return uploaded_file.read().decode("utf-8")
        except UnicodeDecodeError:
            return uploaded_file.read().decode("gbk", errors="replace")
    elif name.endswith(".pdf"):
        import fitz
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        if not text.strip():
            st.warning("该 PDF 未包含可提取的文本内容（可能为扫描件）")
            return ""
        return text
    elif name.endswith(".docx"):
        import docx
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def fetch_url_content(url):
    try:
        import requests
        from bs4 import BeautifulSoup
        resp = requests.get(url, timeout=15)
        resp.encoding = resp.apparent_encoding
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        lines = [line.strip() for line in soup.get_text(separator="\n").splitlines() if line.strip()]
        return "\n".join(lines[:500])
    except Exception as e:
        st.error(f"获取网页内容失败：{e}")
        return ""


def call_llm(client, text, system_prompt, model_name, provider_config):
    try:
        kwargs = dict(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请总结以下内容：\n{text}"},
            ],
            max_tokens=4096,
            temperature=0.6,
        )
        if provider_config["supports_thinking"]:
            kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
        resp = client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content
    except Exception as e:
        st.error(f"API 调用失败：{e}")
        return None


st.set_page_config(page_title="智能文档摘要工具", page_icon="📝")
st.title("📝 智能文档摘要工具")

if "summary" not in st.session_state:
    st.session_state.summary = None
if "summary_tab" not in st.session_state:
    st.session_state.summary_tab = None
if "last_style" not in st.session_state:
    st.session_state.last_style = None

with st.sidebar:
    st.header("使用说明")
    st.markdown(
        """
- **粘贴文本**、**上传文件**或**输入网址**
- AI 会自动识别文档类型，选用最合适的摘要结构
        """
    )
    st.markdown("---")
    style = st.radio("摘要风格", ["标准", "简要", "详细"], horizontal=True)
    if st.session_state.last_style and st.session_state.last_style != style:
        st.session_state.summary = None
        st.session_state.summary_tab = None
        st.rerun()
    st.session_state.last_style = style
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

system_prompt = BASE_PROMPT + STYLE_INSTRUCTIONS[style]

tab1, tab2, tab3 = st.tabs(["📄 粘贴文本", "📁 上传文件", "🔗 输入网址"])

with tab1:
    user_input = st.text_area("把你要总结的文本粘贴到这里：", height=250)
    if st.button("✨ 生成摘要") and user_input.strip():
        with st.spinner("AI 正在阅读并总结..."):
            summary = call_llm(client, user_input, system_prompt, cfg_model, pconf)
        if summary:
            st.session_state.summary = summary
            st.session_state.summary_tab = "paste"
    if st.session_state.summary and st.session_state.summary_tab == "paste":
        st.success("✅ 摘要生成成功！")
        st.markdown(st.session_state.summary)
        fmt = st.selectbox("下载格式", [".md", ".txt"], key="fmt_paste", label_visibility="collapsed")
        st.download_button("📥 下载摘要", st.session_state.summary, file_name=f"summary{fmt}")

with tab2:
    uploaded_file = st.file_uploader("选择文件", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        file_content = read_file_content(uploaded_file)
        if file_content.strip():
            st.code(file_content[:2000], language="text")
            if st.button("✨ 摘要此文件"):
                with st.spinner("AI 正在阅读并总结..."):
                    summary = call_llm(client, file_content, system_prompt, cfg_model, pconf)
                if summary:
                    st.session_state.summary = summary
                    st.session_state.summary_tab = "file"
    if st.session_state.summary and st.session_state.summary_tab == "file":
        st.success("✅ 摘要生成成功！")
        st.markdown(st.session_state.summary)
        fmt = st.selectbox("下载格式", [".md", ".txt"], key="fmt_file", label_visibility="collapsed")
        st.download_button("📥 下载摘要", st.session_state.summary, file_name=f"summary{fmt}")

with tab3:
    url = st.text_input("输入网页链接：", placeholder="https://...")
    if st.button("✨ 摘要此网页") and url.strip():
        with st.spinner("正在获取网页内容..."):
            page_content = fetch_url_content(url)
        if page_content.strip():
            with st.spinner("AI 正在阅读并总结..."):
                summary = call_llm(client, page_content, system_prompt, cfg_model, pconf)
            if summary:
                st.session_state.summary = summary
                st.session_state.summary_tab = "url"
    if st.session_state.summary and st.session_state.summary_tab == "url":
        st.success("✅ 摘要生成成功！")
        st.markdown(st.session_state.summary)
        fmt = st.selectbox("下载格式", [".md", ".txt"], key="fmt_url", label_visibility="collapsed")
        st.download_button("📥 下载摘要", st.session_state.summary, file_name=f"summary{fmt}")

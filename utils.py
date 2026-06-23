from consts import MAX_TEXT_LENGTH, BASE_PROMPT


def truncate_text(text, limit=MAX_TEXT_LENGTH):
    if len(text) > limit:
        return text[:limit]
    return text


def is_valid_url(url):
    return url.startswith(("http://", "https://")) and "." in url


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
        return text
    elif name.endswith(".docx"):
        import docx
        doc = docx.Document(uploaded_file)
        return "\n".join(p.text for p in doc.paragraphs)
    return ""


def fetch_url_content(url):
    import requests
    from bs4 import BeautifulSoup
    resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator="\n")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return truncate_text("\n".join(lines))


def get_zhipu_key():
    import os
    key = os.getenv("ZHIPUAI_API_KEY")
    if not key:
        try:
            import streamlit as st
            key = st.secrets.get("ZHIPUAI_API_KEY")
        except Exception:
            pass
    return key


def call_llm(client, text, system_prompt, model_name, provider_config):
    timeout = max(30, len(text) // 2000 + 30)
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
    for attempt in range(2):
        try:
            resp = client.chat.completions.create(timeout=timeout, **kwargs)
            return resp.choices[0].message.content
        except Exception:
            if attempt == 1:
                raise
    return None


def call_llm_stream(client, text, system_prompt, model_name, provider_config):
    timeout = max(30, len(text) // 2000 + 30)
    kwargs = dict(
        model=model_name,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请总结以下内容：\n{text}"},
        ],
        max_tokens=4096,
        temperature=0.6,
        stream=True,
    )
    if provider_config["supports_thinking"]:
        kwargs["extra_body"] = {"thinking": {"type": "enabled"}}
    if not text.strip():
        return
    try:
        resp = client.chat.completions.create(timeout=timeout, **kwargs)
        for chunk in resp:
            content = chunk.choices[0].delta.content if chunk.choices else None
            if content:
                yield content
    except Exception:
        raise

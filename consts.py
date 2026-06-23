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

MAX_TEXT_LENGTH = 100000
MAX_FILE_SIZE = 50 * 1024 * 1024

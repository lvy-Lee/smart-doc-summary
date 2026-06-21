# 📝 智能文档摘要工具

基于 **Streamlit + OpenAI 兼容 API** 构建的多厂商、多格式智能文档摘要工具，支持自适应文档类型分析与结构化摘要输出。

## 功能特性

- **多格式输入**：支持 TXT / PDF / DOCX 文件上传、文本粘贴、URL 抓取
- **多厂商支持**：智谱AI / DeepSeek / 阿里千问 / 字节豆包 / Kimi / 讯飞星火
- **深度思考**：支持智谱、DeepSeek 等模型的深度推理模式
- **自适应摘要**：AI 自动识别文档类型（小说/技术文档/会议/论文等），选用最合适的摘要结构
- **用户自定义**：可在界面中切换厂商、模型、API Key
- **结果导出**：支持 Markdown / TXT 格式下载

## 技术栈

| 组件 | 技术 |
|---|---|
| Web 框架 | Streamlit |
| API 接入 | OpenAI Python SDK（兼容多厂商） |
| PDF 解析 | PyMuPDF |
| DOCX 解析 | python-docx |
| URL 抓取 | requests + BeautifulSoup |

## 本地运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 创建环境变量文件 .env
ZHIPUAI_API_KEY=your_api_key_here

# 3. 启动
streamlit run app.py
```

## 部署到 Streamlit Cloud

1. 将代码推送到 GitHub
2. 在 [Streamlit Cloud](https://streamlit.io/cloud) 创建新应用
3. 在 Dashboard → **Settings** → **Secrets** 中设置：
   ```toml
   ZHIPUAI_API_KEY = "your_api_key_here"
   ```
4. 部署后访问生成的公网链接

## 项目结构

```
智能文档摘要工具/
├── app.py              # 主程序（Streamlit UI + 业务逻辑）
├── requirements.txt    # 依赖声明
├── .env                # 本地开发环境变量（不上传）
├── .gitignore          # Git 忽略规则
├── .streamlit/
│   └── secrets.toml    # 部署用模板
└── README.md
```

## 支持的厂商及接入地址

| 厂商 | API 地址 | 深度思考 |
|---|---|---|
| 智谱AI | `https://open.bigmodel.cn/api/paas/v4/` | ✅ |
| DeepSeek | `https://api.deepseek.com` | ✅ |
| 阿里千问 | `https://dashscope.aliyuncs.com/compatible-mode/v1` | ❌ |
| 字节豆包 | `https://ark.cn-beijing.volces.com/api/v3/` | ❌ |
| Kimi | `https://api.moonshot.cn/v1` | ❌ |
| 讯飞星火 | `https://spark-api-open.xf-yun.com/v1` | ❌ |

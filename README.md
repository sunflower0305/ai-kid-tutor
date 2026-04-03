<div align="center">

# 🎓 AI Kid Tutor

面向小学生的 AI 学习辅助工具，专注题意理解、作文思路、英语辅导、错题分析。

**不直接给答案，只引导思路** —— 家长和孩子都能接受。

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/sunflower0305/ai-kid-tutor?style=social)](https://github.com/sunflower0305/ai-kid-tutor/stargazers)

</div>

> [!IMPORTANT]
> 如果这个项目对你有帮助，请点 **Star ⭐** 支持一下！你的 Star 是我继续更新的动力。

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📝 作文辅导 | 输入题目，给出思路、好词好句，不代写 |
| 🔤 英语单词 | 输入单词，给出解释 + 例句 + 记忆方法 |
| 🔢 数学题意 | 读不懂题？AI 用通俗语言讲一遍，不直接给答案 |
| ❌ 错题分析 | 输入错题，AI 分析错因 |

---

## 🛠 技术栈

- **前端**：HTML + CSS + JavaScript
- **后端**：Python FastAPI
- **AI**：可插拔多模型（Claude / DeepSeek / Qwen / MiniMax 等）

---

## 🚀 快速开始

```bash
# 1. 安装依赖
cd backend
pip install -r requirements.txt

# 2. 配置环境变量
cp ../.env.example .env
# 编辑 .env，填入你的 API Key

# 3. 启动后端
python main.py

# 4. 打开前端
# 用浏览器直接打开 frontend/index.html
```

## ⚙️ 环境变量

复制 `.env.example` 为 `backend/.env`，按需填入 API Key：

```env
LLM_PROVIDER=minimax   # 可选: claude / qwen / deepseek / glm / doubao / minimax
MINIMAX_API_KEY=你的key
```

---

## 💬 建议 & 联系

有任何想法、功能建议、或者发现 Bug，欢迎：

- 提交 [Issue](https://github.com/sunflower0305/ai-kid-tutor/issues) —— 功能建议、Bug 反馈
- 发起 [Discussion](https://github.com/sunflower0305/ai-kid-tutor/discussions) —— 想法交流、使用心得

也欢迎直接提 PR，一起把这个工具做得更好！

---

## 📄 License

[Apache License 2.0](LICENSE)

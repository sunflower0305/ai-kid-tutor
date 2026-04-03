<div align="center">

# 🎓 AI Kid Tutor

给小学生的 AI 家教 —— 不直接给答案，只启发思路。

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Stars](https://img.shields.io/github/stars/sunflower0305/ai-kid-tutor?style=social)](https://github.com/sunflower0305/ai-kid-tutor/stargazers)

</div>

> [!IMPORTANT]
> 如果这个项目对你有帮助，请点 **Star ⭐** 支持一下！你的 Star 是我继续更新的动力。

---

## ⚡ 最快的用法：Claude Code Skill（推荐）

不需要服务器，不需要配置，**复制一个文件就能用**。

**前提：安装了 [Claude Code](https://claude.ai/code)**

```bash
# 把 skill 文件复制到你的 Claude 配置目录
cp .claude/skills/kid-tutor.md ~/.claude/skills/
```

然后在 Claude Code 里直接输入：

```
/kid-tutor 帮我写关于春天的作文
/kid-tutor apple 这个单词怎么记
/kid-tutor 小明有5个苹果，给了小红2个，还剩几个？
/kid-tutor 我把 10+5 算成了 14，哪里错了
```

就这样，一个 AI 家教到手了。✨

---

## ✨ 功能

| 功能 | 说明 |
|------|------|
| 📝 作文辅导 | 给思路框架和好词好句，绝不代写 |
| 🔤 英语单词 | 解释 + 例句 + 记忆方法 |
| 🔢 数学题意 | 用大白话讲题意，不直接给答案 |
| ❌ 错题分析 | 找出错因，举一反三 |

---

## 🖥 进阶用法：自建服务

如果你是开发者，想把这个工具部署成网页让孩子用：

**技术栈**：HTML + CSS + JS 前端，Python FastAPI 后端，支持多模型切换

```bash
# 安装依赖
cd backend
pip install -r requirements.txt

# 配置 API Key
cp ../.env.example .env
# 编辑 .env，填入你的模型 API Key

# 启动
python main.py

# 打开 frontend/index.html
```

支持的模型：Claude / DeepSeek / Qwen / MiniMax / 豆包 / GLM

---

## 💬 建议 & 联系

有想法、发现 Bug，或者想一起完善这个工具：

- 提 [Issue](https://github.com/sunflower0305/ai-kid-tutor/issues) —— 功能建议、Bug 反馈
- 发起 [Discussion](https://github.com/sunflower0305/ai-kid-tutor/discussions) —— 想法交流
- 邮件：[3268007793@qq.com](mailto:3268007793@qq.com)

---

## 📄 License

[Apache License 2.0](LICENSE)

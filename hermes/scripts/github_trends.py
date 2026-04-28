#!/usr/bin/env python3
"""
GitHub AI 周趋势速报 v3
参考 Get笔记 周报格式：
- 榜单核心趋势（总览）
- 完整榜单解析（表格：排名/项目名称/核心功能/关键特点）
- Top 10 分层解读（工具集成层/核心能力层）
- 关键洞察
"""

import json
import os
import sys
import subprocess
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# ── 配置 ──
DATA_DIR = Path.home() / ".hermes" / "data" / "github-trends"
FEISHU_SCRIPT = Path.home() / ".hermes" / "scripts" / "feishu_send.py"
TOP_N = 20
CHAT_IDS = [
    ("自己", "oc_6dc97fe5ef1e2ede13691456af4a3c66"),
    ("0101", "oc_53db3b1bdc6280ffae4805ba96868eb9"),
]

# 飞书消息有 30000 字符限制，安全起见控制在 25000
MAX_MSG_LEN = 25000


# ── 数据获取 ──

def fetch_html(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        return resp.read().decode()


def fetch_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "Hermes-Agent/1.0",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def scrape_github_trending(since: str = "weekly") -> List[dict]:
    """抓取 GitHub Trending 页面，按本周 star 增长排序"""
    url = f"https://github.com/trending?since={since}"
    html = fetch_html(url)
    
    repos = []
    articles = re.split(r'<article\s+class="Box-row"', html)
    
    for article in articles[1:]:
        repo = {}
        
        # 仓库名
        m = re.search(r'<h2[^>]*>.*?<a[^>]+href="/([^/]+/[^/"]+)"', article, re.DOTALL)
        if m:
            repo["full_name"] = m.group(1).strip()
            repo["url"] = f"https://github.com/{repo['full_name']}"
        
        # 描述
        m = re.search(r'<p\s+class="col-9[^"]*"[^>]*>\s*(.*?)\s*</p>', article, re.DOTALL)
        if m:
            repo["description"] = re.sub(r'<[^>]+>', '', m.group(1)).strip()[:300]
        else:
            repo["description"] = ""
        
        # 语言
        m = re.search(r'itemprop="programmingLanguage"[^>]*>\s*(.*?)\s*<', article)
        repo["language"] = m.group(1).strip() if m else ""
        
        # 本周 star 增长
        m = re.search(r'([\d,]+)\s+stars?\s+this\s+week', article, re.IGNORECASE)
        if not m:
            m = re.search(r'([\d,]+)\s+stars?\s+today', article, re.IGNORECASE)
        repo["weekly_star_growth"] = int(m.group(1).replace(",", "")) if m else 0
        
        # 总 star 数（在 svg star 图标之后的数字）
        m = re.search(r'</svg>\s*([\d,]+)</a>', article)
        repo["stars"] = int(m.group(1).replace(",", "")) if m else 0
        
        if repo.get("full_name"):
            repos.append(repo)
    
    return repos


def fetch_repo_details(full_name: str) -> dict:
    """获取仓库详细信息"""
    details = {}
    try:
        data = fetch_json(f"https://api.github.com/repos/{full_name}")
        details["stars"] = data.get("stargazers_count", 0)
        details["forks"] = data.get("forks_count", 0)
        details["topics"] = data.get("topics", [])
        details["description_en"] = data.get("description", "")
        time.sleep(2)
    except:
        pass
    
    try:
        data = fetch_json(f"https://api.github.com/repos/{full_name}/releases/latest")
        details["latest_release"] = data.get("tag_name", "")
        release_body = (data.get("body") or "").strip()
        # 取 release 说明的第一段作为更新摘要
        if release_body:
            first_para = release_body.split("\n\n")[0][:150]
            details["release_summary"] = first_para
        time.sleep(2)
    except:
        pass
    
    return details


# ── AI 项目分析（核心：人话描述 + 分类 + 特点） ──

# 已知项目的中文描述和分类（手动维护核心项目，其余自动推断）
KNOWN_PROJECTS = {
    "langflow-ai/langflow": {"core_func": "可视化构建和部署AI代理的工作流平台", "key_feature": "拖拽式编排，支持多模型集成和API部署", "desc_long": "Langflow 是基于 Python 的低代码 AI 应用构建平台，提供可视化拖拽界面来编排 AI 工作流。支持集成 OpenAI、Anthropic、HuggingFace 等多种大模型，内置 RAG 引擎和工具调用能力，可一键部署为生产级 API 服务。适合快速搭建 ChatBot、文档问答、多代理协作等应用。", "layer": "tool", "category": "AI代理平台"},
    "langgenius/dify": {"core_func": "生产级AI代理工作流开发平台", "key_feature": "全栈RAG引擎+插件生态，企业级就绪", "desc_long": "Dify 是开源的 LLM 应用开发平台，提供从 Prompt 编排到 RAG 检索增强、Agent 工作流、模型管理的全栈能力。内置向量数据库、文档解析器和 100+ 插件生态，支持 GPT-4、Claude、Llama 等主流模型。企业级特性包括 SSO、审计日志、多租户，已被数千家企业用于生产环境。", "layer": "core", "category": "AI代理平台"},
    "langchain-ai/langchain": {"core_func": "AI代理工程框架", "key_feature": "最成熟的LLM应用开发框架，生态庞大", "desc_long": "LangChain 是 Python/JS 生态中最流行的 LLM 应用开发框架，提供 Chain（链式调用）、Agent（自主决策）、Memory（上下文记忆）、Retriever（知识检索）等核心抽象。拥有 1000+ 集成，LangGraph 支持有状态多代理编排，LangSmith 提供生产监控。", "layer": "core", "category": "LLM开发框架"},
    "browser-use/browser-use": {"core_func": "让AI代理理解和操控网页", "key_feature": "自然语言驱动浏览器自动化，零代码操作", "desc_long": "Browser-Use 让 AI 代理通过自然语言指令自主操控浏览器——理解网页、点击按钮、填写表单、提取数据。底层使用 Playwright，支持视觉理解和 DOM 分析，可集成到 LangChain、AutoGen 等 Agent 框架。是 AI Agent 与 Web 交互的关键基础设施。", "layer": "tool", "category": "浏览器自动化"},
    "infiniflow/ragflow": {"core_func": "开源RAG引擎，深度文档解析", "key_feature": "支持复杂PDF/表格解析，检索准确率高", "desc_long": "RAGFlow 深度文档理解的 RAG 引擎，最大亮点是对复杂文档的精准解析——支持 PDF 表格、图片 OCR、论文公式等非结构化数据。内置 GraphRAG 和 Agentic RAG，搭配自研文档切片策略，检索准确率显著提升。", "layer": "core", "category": "RAG引擎"},
    "OpenHands/OpenHands": {"core_func": "开源AI软件工程代理", "key_feature": "可自主完成issue修复、功能开发等完整工程任务", "desc_long": "OpenHands 是开源 AI 软件工程代理，能自主完成从理解需求到编写代码、运行测试、提交 PR 的完整开发流程。支持多模型，内置沙盒化代码执行环境。在 SWE-Bench 基准测试中表现领先，是 Coding Agent 赛道的标杆项目。", "layer": "core", "category": "AI编程代理"},
    "hiyouga/LlamaFactory": {"core_func": "大模型微调一站式工具", "key_feature": "支持100+模型、多种微调方法，开箱即用", "desc_long": "LlamaFactory 是一站式大模型微调框架，支持 100+ 模型和多种训练方法（SFT、RLHF、DPO、KTO）。集成 LoRA/QLoRA 等参数高效微调策略，提供 Web UI 一键配置，单卡 16GB 即可微调 7B 模型。GitHub 上 Star 最多的中文微调工具。", "layer": "tool", "category": "模型训练"},
    "FlowiseAI/Flowise": {"core_func": "低代码构建LLM应用", "key_feature": "可视化拖拽，快速搭建ChatBot和RAG应用", "desc_long": "Flowise 是拖拽式 LLM 应用编排工具，通过可视化节点连接模型、向量库、工具和数据源，无需编写代码即可构建 ChatBot、RAG 问答、Agent 工作流。支持 100+ 集成，提供 API 端点和嵌入式 Widget。", "layer": "tool", "category": "AI应用构建"},
    "crewAIInc/crewAI": {"core_func": "多AI代理协作框架", "key_feature": "角色扮演式代理团队编排，模拟真实团队协作", "desc_long": "CrewAI 通过定义不同角色（研究员、写手、分析师等）组成 AI 团队，每个代理有独立目标、工具和记忆。支持顺序/层级/协商等协作模式，内置任务委派和结果汇总。适合研究报告生成、代码审查、内容创作等多角色协作场景。", "layer": "core", "category": "多代理框架"},
    "lobehub/lobehub": {"core_func": "一站式AI助手桌面应用", "key_feature": "支持50+模型服务商，插件市场和知识库", "desc_long": "LobeHub 是开源 AI 对话桌面应用，支持 50+ 模型服务商，内置 TTS 语音合成、DALL-E 图像生成、知识库 RAG 和插件市场。提供 ChatGPT-like 界面，支持多会话管理和 Prompt 模板，可一键部署为个人 AI 助手。", "layer": "tool", "category": "AI助手客户端"},
    "mem0ai/mem0": {"core_func": "AI代理的智能记忆层", "key_feature": "跨会话持久记忆，自动去重和关联", "desc_long": "Mem0 为 AI 代理提供持久化记忆，让代理记住用户偏好、历史对话和关键事实。核心能力包括自动提取、智能去重和关联、语义检索。支持主流模型，可搭配 LangChain/CrewAI 使用，解决 LLM 无状态痛点。", "layer": "core", "category": "AI记忆系统"},
    "NousResearch/hermes-agent": {"core_func": "可成长的开源AI代理", "key_feature": "跨会话持久记忆，支持技能扩展和自主学习", "desc_long": "Hermes Agent 是 Nous Research 开源的 AI 代理框架，核心理念是'与用户共同成长'。支持跨会话持久记忆、技能系统、多平台网关（Telegram/Discord/飞书等）。内置工具调用、子代理调度和自主任务执行能力，强调个性化和长期关系建设。", "layer": "core", "category": "AI代理平台"},
    "forrestchang/andrej-karpathy-skills": {"core_func": "Claude Code行为增强配置", "key_feature": "Andrej Karpathy风格的单文件CLAUDE.md配置，优化编程代理行为", "desc_long": "Andrej Karpathy（前 Tesla AI 总监）分享的 Claude Code 最佳实践配置。通过精心设计的 CLAUDE.md 指令优化 AI 编程代理的行为模式——代码风格、测试策略、错误处理和开发工作流。单文件即可显著提升输出质量，引爆 AI 编程社区。", "layer": "tool", "category": "AI编程代理"},
    "microsoft/markitdown": {"core_func": "Office/PDF文档转Markdown工具", "key_feature": "支持Word/Excel/PPT/PDF一键转Markdown，保留格式", "desc_long": "微软开源的文档转换工具，将 Office 和 PDF 转换为干净 Markdown。支持保留表格结构、图片链接和超链接。专为 LLM 和 RAG 场景优化，转换后可直接作为大模型上下文或向量库入库数据，是文档处理流水线的关键组件。", "layer": "tool", "category": "文档工具"},
    "multica-ai/multica": {"core_func": "开源托管式AI代理平台", "key_feature": "将编码代理转化为真实产品，支持团队协作和任务编排", "desc_long": "Multica 将 AI 编程代理从本地工具升级为可远程管理的团队成员。支持任务分配、进度跟踪、代码审查和自动部署。目标是让 AI 代理真正融入开发团队工作流，而非仅作为个人终端工具。", "layer": "core", "category": "AI代理平台"},
    "thedotmack/claude-mem": {"core_func": "Claude Code记忆持久化插件", "key_feature": "自动捕获Claude操作历史，跨会话保持上下文记忆", "desc_long": "Claude-Mem 自动记录 Claude 编程过程中的所有操作——文件修改、命令执行、错误修复和决策过程。跨会话持久保存，下次启动时自动加载上下文，避免重复解释和上下文丢失。", "layer": "tool", "category": "AI记忆系统"},
    "HKUDS/DeepTutor": {"core_func": "AI原生个性化学习助手", "key_feature": "基于RAG的深度辅导系统，支持论文/文档问答和知识追踪", "desc_long": "DeepTutor 是港大数据科学团队开发的 AI 辅导系统，基于 RAG 实现对学术论文和教材的深度理解。能回答复杂文档问题，追踪学习进度，生成个性化学习路径。支持多文档交叉引用和知识图谱构建。", "layer": "core", "category": "AI教育"},
    "coleam00/Archon": {"core_func": "开源AI编码代理框架构建器", "key_feature": "模块化构建自定义编码代理，支持多工具集成", "desc_long": "Archon 是模块化 AI 编码代理构建框架，提供预构建组件（代码生成、测试执行、文件操作、API 调用等），用户可搭积木般组合出定制化编码代理。支持多种 LLM 后端，内置沙盒化执行环境。", "layer": "core", "category": "AI编程代理"},
    "virattt/ai-hedge-fund": {"core_func": "AI对冲基金团队模拟", "key_feature": "多代理协作分析股票：基本面/技术面/风险/情绪", "desc_long": "用多代理架构模拟对冲基金分析师团队：基本面分析师（财报解读）、技术分析师（K线趋势）、风险经理（仓位控制）、情绪分析师（新闻舆情）和投资组合经理（最终决策）。是 AI+金融的标杆项目。", "layer": "tool", "category": "AI金融"},
    "google-ai-edge/gallery": {"core_func": "端侧ML/GenAI用例展示平台", "key_feature": "展示设备端AI应用，支持离线推理和模型部署", "desc_long": "Google AI Edge Gallery 展示在手机/平板上运行 ML 和 GenAI 的用例。包含图像分类、文本生成、语音识别等 Demo，基于 TensorFlow Lite 和 MediaPipe，所有推理在本地完成，保护隐私。", "layer": "tool", "category": "端侧AI"},
    "TheCraigHewitt/seomachine": {"core_func": "Claude Code驱动的SEO内容创作工作流", "key_feature": "自动生成长篇SEO优化内容，结构化写作流程", "desc_long": "SEOMachine 基于 Claude Code 的 SEO 内容自动化工作流，通过结构化代理协作（研究→大纲→写作→优化→审查），自动生成符合 SEO 最佳实践的长篇文章。内置关键词研究、竞品分析、内容结构优化。", "layer": "tool", "category": "AI内容创作"},
    "jo-inc/camofox-browser": {"core_func": "AI代理专用反检测无头浏览器", "key_feature": "隐藏自动化痕迹，让AI代理安全访问各类网站", "desc_long": "Camofox 专为 AI 代理设计，通过指纹伪装、行为模拟和流量混淆，让代理自动化浏览时绕过反爬虫检测。提供统一 API，可与 Agent 框架集成，是 AI 代理访问受限网站的关键基础设施。", "layer": "tool", "category": "浏览器自动化"},
    "msitarzewski/agency-agents": {"core_func": "完整AI代理团队（从前端到社区运营）", "key_feature": "即用型代理团队配置，覆盖CEO/QV/前端/运营等角色", "desc_long": "提供完整的 AI 代理团队配置模板，覆盖 CEO、CTO、前端工程师、后端工程师到社区运营等 20+ 角色。每个代理预设专业 Prompt、工具权限和协作协议，开箱即用，适合快速搭建虚拟团队。", "layer": "tool", "category": "AI代理平台"},
    "addyosmani/agent-skills": {"core_func": "生产级AI编码代理工程技能集", "key_feature": "Google工程师维护，涵盖代码生成/审查/重构的最佳实践", "desc_long": "Google Chrome 工程经理 Addy Osmani 维护的 AI 编码代理最佳实践集合。包含代码生成规范、测试驱动开发、代码审查标准、重构策略和文档模板。可直接加载到 Claude Code、Cursor 等工具中。", "layer": "tool", "category": "AI编程代理"},
    "dzhng/deep-research": {"core_func": "AI深度研究助手", "key_feature": "自动执行多轮网络搜索和信息综合，生成研究报告", "desc_long": "Deep Research 根据用户提问自主规划搜索策略，执行多轮网络搜索，阅读提取网页内容，综合分析后生成带引用的结构化研究报告。类似 Google Gemini Deep Research 但完全开源。", "layer": "core", "category": "AI研究工具"},
    "Comfy-Org/ComfyUI": {"core_func": "节点式AI图像/视频生成工作流", "key_feature": "最强大的Stable Diffusion工作流引擎，模块化", "desc_long": "ComfyUI 是基于节点图的 AI 图像/视频生成工具，通过可视化连线编排 SD、SDXL、Flux 等模型。支持 ControlNet、IP-Adapter、LoRA、AnimateDiff 等高级功能，社区提供数千种预设工作流，是 AI 创作专业人士的首选。", "layer": "tool", "category": "图像生成"},
    "google-gemini/gemini-cli": {"core_func": "Gemini驱动的命令行AI代理", "key_feature": "终端原生集成，支持文件操作和命令执行", "desc_long": "Google 官方推出的命令行 AI 编程代理，将 Gemini 模型能力带到终端。支持文件读写、Shell 命令执行、代码搜索和项目级上下文理解。内置 MCP 支持，类似于 Claude Code 但基于 Gemini 模型家族。", "layer": "core", "category": "AI编程代理"},
    "Shubhamsaboo/awesome-llm-apps": {"core_func": "LLM应用合集（含Agent和RAG示例）", "key_feature": "覆盖OpenAI/Anthropic/Gemini多平台实战案例", "desc_long": "精选大语言模型应用代码合集，涵盖 AI Agent、RAG、ChatBot、工具调用等多种场景。每个示例包含完整可运行代码，支持多平台。是学习 LLM 应用开发的实战教程库，入门到进阶的必备资源。", "layer": "tool", "category": "AI应用集合"},
    "x1xhlol/system-prompts-and-models-of-ai-tools": {"core_func": "主流AI编程工具的系统提示词集合", "key_feature": "收集Cursor/Devin/Claude Code等内部提示词，可参考学习", "desc_long": "收集了市面上主流 AI 编程工具的系统提示词，包括 Cursor、Devin、Claude Code、Bolt、v0 等产品的内部指令。通过研究这些提示词可以了解商业 AI 工具如何通过指令控制模型行为，是 Prompt Engineering 的实战参考。", "layer": "tool", "category": "AI提示词"},
}


def analyze_repo(repo: dict) -> dict:
    """
    分析项目：核心功能、关键特点、详细描述、分类、层次。
    已知项目用预设数据，未知项目自动推断。
    """
    name = repo["full_name"]
    
    if name in KNOWN_PROJECTS:
        info = KNOWN_PROJECTS[name].copy()
    else:
        # 自动推断
        desc = repo.get("description_en") or repo.get("description") or ""
        topics = repo.get("topics", [])
        text = (desc + " " + " ".join(topics)).lower()
        
        # 核心功能 = 描述的第一句话
        core_func = desc.split(".")[0].strip() if "." in desc else desc
        if len(core_func) > 50:
            core_func = core_func[:47] + "..."
        
        # 分类推断
        category = "AI工具"
        cat_map = {
            "AI代理平台": ["agent", "workflow", "agentic"],
            "LLM开发框架": ["llm framework", "chain", "langchain"],
            "RAG引擎": ["rag", "retrieval", "knowledge"],
            "AI编程代理": ["code", "coding", "copilot"],
            "模型训练": ["training", "fine-tun", "lora"],
            "图像生成": ["diffusion", "image", "text-to-image"],
            "AI助手客户端": ["chat", "assistant", "chatbot"],
            "多代理框架": ["multi-agent", "crew"],
            "大语言模型": ["llm", "language model", "gpt"],
            "AI教程": ["course", "tutorial", "beginner"],
        }
        for cat, keywords in cat_map.items():
            if any(kw in text for kw in keywords):
                category = cat
                break
        
        # 关键特点 = 精简描述
        key_feature = desc[:60] if desc else "暂无详细描述"
        
        # 层次推断
        layer = "core" if any(kw in text for kw in ["framework", "engine", "platform", "model"]) else "tool"
        
        # 详细描述（~100字）：组合 GitHub 描述 + topics + 最新 release
        desc_long_parts = []
        if desc:
            desc_long_parts.append(desc)
        if topics:
            desc_long_parts.append(f"技术栈: {', '.join(topics[:5])}")
        if repo.get("latest_release"):
            desc_long_parts.append(f"最新版本: {repo['latest_release']}")
        if repo.get("release_summary"):
            desc_long_parts.append(repo["release_summary"][:80])
        desc_long = "。".join(desc_long_parts) if desc_long_parts else "暂无详细描述。"
        if len(desc_long) > 150:
            desc_long = desc_long[:147] + "..."
        
        info = {
            "core_func": core_func,
            "key_feature": key_feature,
            "desc_long": desc_long,
            "layer": layer,
            "category": category,
        }
    
    # 合并 release 信息到 key_feature
    if repo.get("release_summary"):
        info["key_feature"] += f" | 最新: {repo.get('latest_release', '')}"
    
    return info


# ── 排名趋势 ──

def load_snapshot(date_str: str) -> Optional[dict]:
    path = DATA_DIR / f"{date_str}.json"
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def save_snapshot(date_str: str, repos: List[dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"{date_str}.json"
    data = {
        "date": date_str,
        "repos": [{
            "rank": i + 1,
            "full_name": r["full_name"],
            "stars": r.get("stars", 0),
            "weekly_star_growth": r.get("weekly_star_growth", 0),
        } for i, r in enumerate(repos)]
    }
    with open(path, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def compute_rank_changes(current: List[dict], prev_snapshot: Optional[dict]) -> dict:
    """返回 {full_name: rank_change} 正数=上升"""
    if not prev_snapshot:
        return {}
    prev_map = {r["full_name"]: r["rank"] for r in prev_snapshot["repos"]}
    changes = {}
    for i, r in enumerate(current):
        name = r["full_name"]
        if name in prev_map:
            changes[name] = prev_map[name] - (i + 1)
        else:
            changes[name] = None  # 新上榜
    return changes


def trend_tag(change: Optional[int]) -> str:
    if change is None:
        return "🆕"
    if change > 3:
        return f"🔥+{change}"
    elif change > 0:
        return f"↑{change}"
    elif change < -3:
        return f"❄️{change}"
    elif change < 0:
        return f"↓{change}"
    return "→"


# ── 报告生成 ──

def generate_report(repos: List[dict], analyses: List[dict],
                    week_changes: dict, day_changes: dict,
                    date_str: str) -> dict:
    """
    生成完整报告，返回两种格式：
    - 'markdown': 完整 Markdown（用于飞书文档）
    - 'summary': 精简文本摘要（用于聊天消息，附文档链接）
    """
    
    now = datetime.now()
    week_num = now.isocalendar()[1]
    max_growth = max((r.get("weekly_star_growth", 0) for r in repos), default=1)
    newcomers = sum(1 for c in week_changes.values() if c is None)
    top = repos[0] if repos else None
    total_growth = sum(r.get("weekly_star_growth", 0) for r in repos)
    
    # ── Markdown 版（飞书文档） ──
    md_lines = []
    md_lines.append(f"# GitHub AI 热榜 2026-W{week_num}")
    md_lines.append(f"**{date_str}** | 数据源: GitHub Trending Weekly")
    md_lines.append("")
    
    # 核心数字
    md_lines.append("## 🔥 本周概览")
    md_lines.append("")
    md_lines.append(f"- **总增长**: +{total_growth:,}⭐")
    md_lines.append(f"- **新上榜**: {newcomers} 个")
    if top:
        md_lines.append(f"- **增长冠军**: {top['full_name']} (+{top.get('weekly_star_growth', 0):,}⭐)")
    md_lines.append("")
    
    # 领域热度分布
    md_lines.append("## 📊 领域热度分布")
    md_lines.append("")
    cat_growth = {}
    for repo, a in zip(repos, analyses):
        cat = a["category"]
        cat_growth[cat] = cat_growth.get(cat, 0) + repo.get("weekly_star_growth", 0)
    sorted_cats = sorted(cat_growth.items(), key=lambda x: x[1], reverse=True)
    max_cat = sorted_cats[0][1] if sorted_cats and sorted_cats[0][1] > 0 else 1
    
    md_lines.append("| 领域 | 本周增长 | 热度 |")
    md_lines.append("|------|---------|------|")
    for cat, growth in sorted_cats:
        bar_len = int(growth / max_cat * 10) if max_cat > 0 else 0
        bar = "█" * bar_len + "░" * (10 - bar_len)
        md_lines.append(f"| {cat} | +{growth:,} | {bar} |")
    md_lines.append("")
    
    # 完整榜单
    md_lines.append("## 🏆 完整榜单 Top 20")
    md_lines.append("")
    md_lines.append("| # | 趋势 | 项目 | ⭐ 总Star | 📈 本周增长 | 分类 |")
    md_lines.append("|---|------|------|----------|-----------|------|")
    
    for i, repo in enumerate(repos):
        rank = i + 1
        name = repo["full_name"].split("/")[-1]
        a = analyses[i]
        growth = repo.get("weekly_star_growth", 0)
        stars = repo.get("stars", 0)
        
        wc = week_changes.get(repo["full_name"])
        if wc is None:
            trend = "🆕NEW"
        elif wc > 3:
            trend = f"🔥+{wc}"
        elif wc > 0:
            trend = f"↑+{wc}"
        elif wc < -3:
            trend = f"❄️{wc}"
        elif wc < 0:
            trend = f"↓{wc}"
        else:
            trend = "→"
        
        growth_str = f"+{growth:,}" if growth > 0 else "-"
        stars_str = f"{stars//1000}k" if stars >= 1000 else str(stars)
        
        md_lines.append(f"| {rank} | {trend} | **{name}** | {stars_str} | {growth_str} | {a['category']} |")
    
    md_lines.append("")
    
    # 项目详细讲解
    md_lines.append("## 📖 项目详解")
    md_lines.append("")
    
    for i, repo in enumerate(repos):
        rank = i + 1
        name = repo["full_name"].split("/")[-1]
        a = analyses[i]
        growth = repo.get("weekly_star_growth", 0)
        stars = repo.get("stars", 0)
        
        stars_str = f"⭐{stars//1000}k" if stars >= 1000 else f"⭐{stars}"
        growth_str = f"📈本周+{growth:,}" if growth > 0 else ""
        desc_long = a.get("desc_long", a["core_func"])
        
        md_lines.append(f"**{rank}. {name}** {stars_str} {growth_str} [{a['category']}]")
        md_lines.append(f"{desc_long}")
        md_lines.append("")
    
    # 关键洞察
    md_lines.append("## 💡 关键洞察")
    md_lines.append("")
    
    rising = [(r["full_name"].split("/")[-1], c) for r, c in zip(repos, week_changes.values()) if c and c > 2]
    falling = [(r["full_name"].split("/")[-1], c) for r, c in zip(repos, week_changes.values()) if c and c < -2]
    new_names = [r["full_name"].split("/")[-1] for r, c in zip(repos, week_changes.values()) if c is None][:5]
    
    if rising:
        md_lines.append("**🔺 上升最快:**")
        for n, c in sorted(rising, key=lambda x: -x[1])[:5]:
            md_lines.append(f"- {n} (+{c})")
        md_lines.append("")
    if falling:
        md_lines.append("**🔻 下降最多:**")
        for n, c in sorted(falling, key=lambda x: x[1])[:5]:
            md_lines.append(f"- {n} ({c})")
        md_lines.append("")
    if new_names:
        md_lines.append("**🆕 新上榜:**")
        for n in new_names:
            md_lines.append(f"- {n}")
        md_lines.append("")
    
    md_lines.append(f"*生成时间: {now.strftime('%Y-%m-%d %H:%M')}*")
    
    markdown = "\n".join(md_lines)
    
    # ── 精简摘要（飞书聊天消息） ──
    summary_lines = []
    summary_lines.append(f"📊 GitHub AI 热榜 W{week_num} ({date_str})")
    summary_lines.append(f"总增长 +{total_growth:,}⭐ | 新上榜 {newcomers} 个")
    if top:
        summary_lines.append(f"冠军: {top['full_name']} +{top.get('weekly_star_growth', 0):,}⭐")
    summary_lines.append("")
    summary_lines.append("Top 5:")
    for i, repo in enumerate(repos[:5]):
        name = repo["full_name"].split("/")[-1]
        growth = repo.get("weekly_star_growth", 0)
        growth_str = f"+{growth:,}" if growth > 0 else ""
        summary_lines.append(f"  {i+1}. {name} {growth_str}")
    
    summary = "\n".join(summary_lines)
    
    return {"markdown": markdown, "summary": summary}


# ── 飞书发送 ──

# ── 飞书文档 ──

def get_feishu_token() -> str:
    """获取飞书 tenant_access_token"""
    env_path = os.path.expanduser("~/.hermes/.env")
    app_id = app_secret = None
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line.startswith("FEISHU_APP_ID="):
                app_id = line.split("=", 1)[1]
            elif line.startswith("FEISHU_APP_SECRET="):
                app_secret = line.split("=", 1)[1]
    
    data = json.dumps({"app_id": app_id, "app_secret": app_secret}).encode()
    req = Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=data, headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urlopen(req, timeout=10).read())
    return resp["tenant_access_token"]


def create_feishu_doc(token: str, title: str) -> str:
    """创建飞书文档，返回 document_id"""
    data = json.dumps({"title": title, "folder_token": ""}).encode()
    req = Request(
        "https://open.feishu.cn/open-apis/docx/v1/documents",
        data=data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    )
    resp = json.loads(urlopen(req, timeout=15).read())
    return resp["data"]["document"]["document_id"]


def text_run(content: str, bold: bool = False) -> dict:
    """构建飞书 text_run"""
    return {
        "text_run": {
            "content": content,
            "text_element_style": {"bold": bold}
        }
    }


def markdown_to_feishu_blocks(markdown: str) -> List[dict]:
    """将 Markdown 转换为飞书文档 blocks"""
    blocks = []
    
    for line in markdown.split("\n"):
        stripped = line.strip()
        
        if not stripped:
            continue
        
        # 分割线
        if stripped == "---" or stripped == "***":
            blocks.append({"block_type": 22, "divider": {}})
            continue
        
        # H1
        if stripped.startswith("# ") and not stripped.startswith("## "):
            text = stripped[2:]
            blocks.append({
                "block_type": 3,
                "heading1": {
                    "elements": _parse_inline(text),
                    "style": {}
                }
            })
            continue
        
        # H2
        if stripped.startswith("## "):
            text = stripped[3:]
            blocks.append({
                "block_type": 4,
                "heading2": {
                    "elements": _parse_inline(text),
                    "style": {}
                }
            })
            continue
        
        # H3
        if stripped.startswith("### "):
            text = stripped[4:]
            blocks.append({
                "block_type": 5,
                "heading3": {
                    "elements": _parse_inline(text),
                    "style": {}
                }
            })
            continue
        
        # 代码块（简化处理：当作普通文本）
        if stripped.startswith("```"):
            continue
        
        # 列表项（飞书 bullet 类型有兼容问题，用普通文本 + 前缀）
        if stripped.startswith("- "):
            text = stripped[2:]
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": [text_run("• ")] + _parse_inline(text),
                    "style": {}
                }
            })
            continue
        
        # 表格行（简化：转为普通文本）
        if stripped.startswith("|") and "|" in stripped[1:]:
            # 跳过分隔行
            if set(stripped.replace("|", "").replace("-", "").replace(":", "").strip()) == set():
                continue
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            table_text = "  |  ".join(cells)
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": [text_run(table_text)],
                    "style": {}
                }
            })
            continue
        
        # 斜体（*text*）
        if stripped.startswith("*") and stripped.endswith("*") and not stripped.startswith("**"):
            blocks.append({
                "block_type": 2,
                "text": {
                    "elements": _parse_inline(stripped),
                    "style": {}
                }
            })
            continue
        
        # 普通段落
        blocks.append({
            "block_type": 2,
            "text": {
                "elements": _parse_inline(stripped),
                "style": {}
            }
        })
    
    return blocks


def _parse_inline(text: str) -> List[dict]:
    """解析行内 Markdown（**bold**, *italic*）为飞书 elements"""
    elements = []
    i = 0
    while i < len(text):
        # **bold**
        if text[i:i+2] == "**":
            end = text.find("**", i + 2)
            if end > 0:
                elements.append(text_run(text[i+2:end], bold=True))
                i = end + 2
                continue
        # *italic* — 飞书没有 italic，用普通文本
        if text[i] == "*" and i + 1 < len(text):
            end = text.find("*", i + 1)
            if end > 0 and end > i + 1:
                elements.append(text_run(text[i+1:end]))
                i = end + 1
                continue
        # 普通字符 — 收集连续的普通文本
        j = i
        while j < len(text) and text[j] not in "*":
            j += 1
        if j > i:
            elements.append(text_run(text[i:j]))
        i = max(j, i + 1)
    
    return elements if elements else [text_run(text)]


def add_blocks_to_doc(token: str, doc_id: str, blocks: List[dict], batch_size: int = 30):
    """批量添加 blocks 到飞书文档（API 限制每次最多 50 个）"""
    for i in range(0, len(blocks), batch_size):
        batch = blocks[i:i+batch_size]
        body = json.dumps({"children": batch, "index": 0}).encode()
        req = Request(
            f"https://open.feishu.cn/open-apis/docx/v1/documents/{doc_id}/blocks/{doc_id}/children?document_revision_id=-1",
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
        )
        try:
            resp = json.loads(urlopen(req, timeout=30).read())
            if resp["code"] != 0:
                print(f"[WARN] Batch {i//batch_size}: code={resp['code']}, msg={resp['msg']}")
        except Exception as e:
            print(f"[ERROR] Batch {i//batch_size}: {e}")
        time.sleep(0.5)


def send_doc_link_to_feishu(token: str, chat_id: str, doc_id: str, title: str, summary: str):
    """发送飞书文档链接卡片到聊天"""
    doc_url = f"https://feishu.cn/docx/{doc_id}"
    content = {
        "header": {"title": {"tag": "plain_text", "content": title}},
        "elements": [
            {"tag": "div", "text": {"tag": "plain_text", "content": summary}},
            {"tag": "action", "actions": [{
                "tag": "button",
                "text": {"tag": "plain_text", "content": "📖 查看完整报告"},
                "url": doc_url,
                "type": "primary"
            }]}
        ]
    }
    body = json.dumps({
        "receive_id": chat_id,
        "msg_type": "interactive",
        "content": json.dumps(content)
    }).encode()
    req = Request(
        "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}"
        }
    )
    try:
        resp = json.loads(urlopen(req, timeout=15).read())
        return resp["code"] == 0
    except Exception as e:
        print(f"[ERROR] 发送卡片失败 ({chat_id}): {e}")
        return False


def send_to_feishu(message: str, chat_id: str) -> bool:
    """通过飞书发送纯文本消息"""
    cmd = ["python3", str(FEISHU_SCRIPT), "--chat-id", chat_id, "--", message]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"[ERROR] 飞书发送失败 ({chat_id}): {result.stderr}", file=sys.stderr)
        return False
    return True


# ── 主流程 ──

def search_ai_repos_supplement() -> List[dict]:
    """搜索近期活跃的 AI 项目，补充 trending 不足的部分"""
    repos = {}
    
    queries = [
        "artificial+intelligence+pushed:>2026-04-01+stars:>5000",
        "large+language+model+pushed:>2026-04-01+stars:>3000",
        "AI+agent+pushed:>2026-04-01+stars:>2000",
        "generative+AI+pushed:>2026-04-01+stars:>2000",
        "AI+coding+OR+code+agent+pushed:>2026-04-01+stars:>1000",
    ]
    
    for query in queries:
        url = (
            f"https://api.github.com/search/repositories"
            f"?q={query}&sort=stars&order=desc&per_page=20"
        )
        try:
            data = fetch_json(url)
            for item in data.get("items", []):
                name = item["full_name"]
                if name not in repos:
                    repos[name] = {
                        "full_name": name,
                        "description": (item.get("description") or "")[:300],
                        "stars": item["stargazers_count"],
                        "language": item.get("language") or "",
                        "topics": item.get("topics", []),
                        "url": item["html_url"],
                        "weekly_star_growth": 0,
                    }
            time.sleep(3)
        except Exception as e:
            print(f"[WARN] 补充搜索失败: {e}", file=sys.stderr)
    
    return list(repos.values())


# 非 AI 项目黑名单关键词
NON_AI_SIGNALS = [
    "textbook", "curriculum", "education-china", "chinese-textbook",
    "interview", "roadmap", "awesome-mac", "awesome-windows",
    "free-programming", "coding-interview", "system-design",
    "30-seconds-of", "clean-code", "developer-roadmap",
    "the-art-of", "build-your-own", "javascript-algorithms",
]


def is_ai_related(repo: dict) -> bool:
    """判断项目是否与 AI 相关"""
    name = (repo.get("full_name") or "").lower()
    desc = (repo.get("description") or "").lower()
    topics = [t.lower() for t in repo.get("topics", [])]
    text = name + " " + desc + " " + " ".join(topics)
    
    # 排除明确的非 AI 项目
    if any(sig in text for sig in NON_AI_SIGNALS):
        return False
    
    # AI 相关关键词
    ai_signals = [
        "ai", "llm", "gpt", "machine-learning", "deep-learning",
        "neural", "transformer", "agent", "rag", "diffusion",
        "language-model", "inference", "fine-tune", "training",
        "nlp", "computer-vision", "ml", "generative", "chatbot",
        "embedding", "vector", "coding-agent", "code-agent",
        "claude", "copilot", "cursor", "codex",
    ]
    return any(sig in text for sig in ai_signals)


def main():
    today = datetime.now()
    today_str = today.strftime("%Y-%m-%d")
    yesterday_str = (today - timedelta(days=1)).strftime("%Y-%m-%d")
    week_ago_str = (today - timedelta(days=7)).strftime("%Y-%m-%d")
    
    print(f"[INFO] 开始抓取 GitHub AI 周趋势... ({today_str})")
    
    # 1. 抓取 Trending（带重试和降级）
    print("[INFO] 抓取 GitHub Trending weekly...")
    trending_repos = []
    for attempt in range(3):
        try:
            trending_repos = scrape_github_trending("weekly")
            print(f"[INFO] Trending 获取 {len(trending_repos)} 个")
            break
        except (HTTPError, URLError) as e:
            wait = 30 * (attempt + 1)
            print(f"[WARN] Trending 抓取失败 (尝试 {attempt+1}/3): {e}. 等待 {wait}s 后重试...", file=sys.stderr)
            if attempt < 2:
                time.sleep(wait)
            else:
                print(f"[WARN] Trending 持续不可用，降级到纯 API 搜索模式", file=sys.stderr)
    
    # 2. 补充搜索（trending 不足 20 时，或 trending 完全失败时）
    all_repos = {r["full_name"]: r for r in trending_repos}
    if len(all_repos) < TOP_N:
        print("[INFO] 补充搜索活跃 AI 项目...")
        time.sleep(3)
        search_repos = search_ai_repos_supplement()
        for r in search_repos:
            if r["full_name"] not in all_repos:
                all_repos[r["full_name"]] = r
        print(f"[INFO] 合计 {len(all_repos)} 个")
    
    # 3. 过滤非 AI 项目
    ai_repos = {name: r for name, r in all_repos.items() if is_ai_related(r)}
    print(f"[INFO] AI 相关项目: {len(ai_repos)} 个")
    
    # 4. 排序：trending 优先（有周增长），其次按 star
    repos = sorted(
        ai_repos.values(),
        key=lambda r: (r.get("weekly_star_growth", 0), r.get("stars", 0)),
        reverse=True
    )[:TOP_N]
    
    # 3. 获取详情 + 分析
    print(f"[INFO] 分析项目...")
    analyses = []
    for i, repo in enumerate(repos):
        name = repo["full_name"]
        print(f"  [{i+1}/{len(repos)}] {name}...", end=" ", flush=True)
        
        # 获取补充信息（仅对缺少描述的）
        if not repo.get("description"):
            details = fetch_repo_details(name)
            repo.update(details)
        
        analysis = analyze_repo(repo)
        analyses.append(analysis)
        
        growth = repo.get("weekly_star_growth", 0)
        print(f"+{growth}⭐ [{analysis['category']}]")
    
    # 4. 计算排名变化
    day_snapshot = load_snapshot(yesterday_str)
    week_snapshot = load_snapshot(week_ago_str)
    day_changes = compute_rank_changes(repos, day_snapshot)
    week_changes = compute_rank_changes(repos, week_snapshot)
    
    # 5. 生成报告
    report = generate_report(repos, analyses, week_changes, day_changes, today_str)
    markdown = report["markdown"]
    summary = report["summary"]
    
    week_num = today.isocalendar()[1]
    print("\n" + "=" * 50)
    print(summary)
    print("=" * 50)
    
    # 6. 保存快照
    save_snapshot(today_str, repos)
    print(f"\n[INFO] 快照已保存")
    
    # 7. 发送飞书
    if "--send" in sys.argv:
        print("[INFO] 创建飞书文档...")
        token = get_feishu_token()
        title = f"GitHub AI 热榜 2026-W{week_num} ({today_str})"
        
        # 创建文档
        doc_id = create_feishu_doc(token, title)
        doc_url = f"https://feishu.cn/docx/{doc_id}"
        print(f"[INFO] 文档已创建: {doc_url}")
        
        # 写入内容
        blocks = markdown_to_feishu_blocks(markdown)
        print(f"[INFO] 写入 {len(blocks)} 个 blocks...")
        add_blocks_to_doc(token, doc_id, blocks)
        print(f"[INFO] 内容写入完成")
        
        # 发送文档链接卡片到各聊天
        for label, chat_id in CHAT_IDS:
            print(f"[INFO] 发送文档卡片到 [{label}] {chat_id}...")
            success = send_doc_link_to_feishu(token, chat_id, doc_id, title, summary)
            print(f"[INFO] {'✅ 成功' if success else '❌ 失败'}")
    else:
        print("\n[INFO] 预览模式。用 --send 推送。")
        print(f"\n--- Markdown 预览 ---\n{markdown[:500]}...")


if __name__ == "__main__":
    main()

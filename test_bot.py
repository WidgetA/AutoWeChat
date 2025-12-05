# -*- coding: utf-8 -*-
import requests
import webbrowser
import time

url = "http://localhost:8080/api/process"

# 您提供的真实长文本
content = """Meta 或大规模采用 TPU，Alphabet 走高而英伟达承压，算力格局出现新的不确定性
据 The Information 报道，Meta 正与 Google 洽谈在 2027 年起于自家数据中心大规模采用 Google 的 TPU，投入规模可能达到数十亿美元，同时评估自明年起通过 Google Cloud 租用 TPU 集群。当前 Meta 的训练基础设施主要依赖英伟达 H 系列 GPU，而 Google 近期已与 Anthropic 达成最多 100 万颗 TPU 的供应协议。如果此次交易落地，将使 TPU 成为 Meta 在英伟达之外的第二条算力供应链。
消息发布后，Alphabet 盘后上涨约 2.7%，英伟达下跌约 2.7%，市场将其视为 AI 加速器供给格局可能出现松动的迹象。双方均未置评。

Insights
这一动向背后反映出大型模型开发者对算力成本结构和供应链风险的重新评估。随着模型规模扩大、推理流量增长，完全依赖英伟达 GPU 使 Meta 在产能、价格与交付周期上承受不确定性。引入 TPU 可能形成跨架构调度的长期方案，使训练与推理在不同阶段分流，以提高整体资源的可控性。
从供给侧看，TPU 若在 Meta 的生产环境中获得验证，将推动其从 Google 内部产品走向更加产业化的角色，补上 GPU 与各类 ASIC 之间的第二条主流路线。这对 Google 意味着技术栈的进一步外部化：TPU 的软件层、编译器与执行框架需要适配跨公司 workload，而不再仅围绕自家 Gemini 模型优化，可能加速 OpenXLA 等工具链的开放化演进。
对于行业结构，这一事件强化了“多架构并存”的趋势。2023–2024 年 GPU 一统格局开始松动，头部公司正把算力视为类似能源的基础资源，需要通过多路线降低单厂商风险。未来几年，英伟达仍保持主导，但 TPU、自研加速器和专用 ASIC 可能共同构成供给体系，使算力竞争从“芯片之争”转向“硬件架构 + 编译器层 + 模型路线”的综合竞争框架。
整体来看，Meta 与 Google 的接洽不仅是一项采购评估，更是 AI 基础设施在成本、可扩展性与供应链治理层面的结构性调整。它提示行业正在从单一硬件范式转向更分散、更可组合的计算架构，尤其在大模型时代训练成本边际变化愈发敏感的背景下，这类多架构策略可能成为主流。"""

data = {
    "text": content,
    # 强制指定关键词，确保封面图是 Meta 和 Google 的 Logo
    "keywords": ["Meta", "Google"] 
}

print("🤖 正在提交任务 (Meta x Google)...")

try:
    resp = requests.post(url, json=data)
    
    if resp.status_code == 200:
        result = resp.json()
        print("\n✅ 生成成功！")
        print(f"🖼 封面图: {result['cover_url']}")
        print(f"📄 公众号文章: {result['html_url']}")
        webbrowser.open(result['html_url'])
    else:
        print("❌ 服务器报错:", resp.text)
    
except Exception as e:
    print("❌ 连接错误:", e)
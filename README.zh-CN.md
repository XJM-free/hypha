# Hypha

> **Agent 脚下的菌丝网络。**
> 为 Claude Code、Codex、Cursor、Aider、OpenClaw 共享的自我进化 playbook。

[English](README.md) · [中文](README.zh-CN.md)

---

## 为什么需要 Hypha

2026 年 4 月的 SWE-bench Verified，榜首用自定义 scaffold 拿到 **93.9%**。
同一个模型在 SEAL 标准化 scaffold 下只有 **45.9%**。

> Scaffold 值 10 分以上。Scaffold 本身就是产品。

而另一边，每个 agent 都在忘掉昨天学到的东西。你把同一条"别 mock 数据库"的经验
粘贴进 CLAUDE.md、Cursor rules、Codex 的 AGENTS.md、Aider 的 conventions——五个地方，
五份副本，慢慢就漂移了。

Hypha 是所有这些 agent 脚下共同的那一层。

## 它做什么

四种能力，一个目录对应一个 CLI 命令：

| 能力 | 命令 | 灵感来源 |
|---|---|---|
| **Consolidate** 合并——把零散笔记整理成**非破坏性、可版本化**的 playbook | `hypha consolidate` | [ACE](https://arxiv.org/abs/2510.04618) · [Anthropic Auto Dream](https://claude.com/blog/claude-managed-agents-memory) |
| **Reflect** 反思——失败后定位第一个错误步骤并写下教训 | `hypha reflect` | [Reflexion](https://arxiv.org/abs/2303.11366) · [Agent-R](https://arxiv.org/abs/2501.11425) |
| **Harvest** 沉淀——成功后抽取可复用 skill 到 inbox 等待审批 | `hypha harvest` | [Voyager](https://voyager.minedojo.org) · [Gemini CLI /memory inbox](https://cloud.google.com/blog/products/ai-machine-learning) |
| **Guard** 守门——改 playbook 前先跑小 benchmark；退步则回滚 | `hypha guard` | [DGM](https://sakana.ai/dgm) · [SWE-Skills-Bench](https://arxiv.org/abs/2603.15401) |

所有东西以 Markdown 形式落盘。Git 就是你的审计日志。**不需要向量数据库**。

## 设计原则

1. **Markdown 是基座。** 这和 Anthropic 2026 年 4 月给
   [Managed Agents 挂载文件系统 memory](https://claude.com/blog/claude-managed-agents-memory)
   的路线一致。每一条记忆都能 `grep` / `diff` / `git blame`。
2. **LLM 永远不 DELETE。** 它只能提议新增和标记旧条目"已被覆盖"，真正归档由人或下一轮会话做。
   这是**故意的不对称**——丢掉一条血泪教训的代价远高于多留一条旧条目。
3. **Monorepo，薄 adapter。** 算法是与 agent 无关的；每个 agent 只需要一个 &lt;200 行的适配器，
   把原生 lifecycle 事件接到 `hypha <cmd>`。
4. **Embedding 可选。** skill 数量 &lt; 200 时，grep + description 比向量检索更快、更简单、更可审阅。
   Mem0 / FAISS 后续可以作为插件式索引接入——不是重写。

## 快速开始

```bash
pip install hypha-agent   # 即将上架；当前:
git clone https://github.com/XJM-free/hypha && cd hypha && pip install -e .

# 为当前项目初始化 memory
hypha init

# 把散落的笔记整理成 playbook
hypha consolidate

# 审阅最近会话沉淀的 skill
hypha inbox
```

## 支持的 Agent

| Agent | 状态 | Lifecycle 机制 |
|---|---|---|
| [Claude Code](adapters/claude-code/) | ✅ P0 | `~/.claude/settings.json` hooks |
| [OpenAI Codex](adapters/codex/) | 🚧 P1 | `AGENTS.md` + `.codex/` |
| [Cursor](adapters/cursor/) | 🚧 P1 | `.cursor/rules/` + post-commit |
| [OpenClaw](adapters/openclaw/) | 🚧 P1 | 待定——原生集成 |
| Aider, OpenHands, Cline | 📋 P2 | 欢迎社区贡献 |

## 架构

```
                 ┌────────────────────────────────────┐
                 │         hypha CLI                   │
                 │  consolidate · reflect · harvest ·  │
                 │           guard · inbox             │
                 └──────────────────┬─────────────────┘
                                    │
          ┌────────────┬────────────┼────────────┬────────────┐
          ▼            ▼            ▼            ▼            ▼
    Claude Code    OpenAI       Cursor       OpenClaw       ...
     adapter      Codex adapt   adapter       adapter
          │            │            │            │
          └────────────┴────────────┴────────────┴──────────►
                                                              ~/.hypha/
                                                              ├── memory/
                                                              ├── skills/
                                                              ├── reflections/
                                                              └── bench/
```

## 路线图

- **v0.1**（现在）—— Claude Code adapter、4 个核心算法、tiny bench
- **v0.2** —— Codex + Cursor adapter、SWE-Skills-Bench 集成、inbox UX 打磨
- **v0.3** —— 可选 Mem0 / FAISS 索引后端、ACE playbook 导入
- **v0.4** —— Managed Agents connector（`managed-agents-2026-04-01` header）
- **v1.0** —— OpenClaw + Aider + OpenHands adapter、稳定 CLI

## 坦诚的局限

Hypha 是一个**非元认知（non-metacognitive）**的自我进化系统。它能进化 agent 的
memory、skills 和护栏，但**不会进化 hook 本身**。像
[HyperAgents / DGM-H](https://arxiv.org/abs/2603.19461) 这类框架追求完全的元认知自我修改；
我们**故意不做**。我们相信一个**可靠、可审计**的 baseline 比一个无边界但脆弱的系统更有用。
如果你需要后者，去读
[Position: Truly Self-Improving Agents Require Intrinsic Metacognitive Learning](https://openreview.net/forum?id=4KhDd0Ozqe)（ICLR 2026）。

另外：2026 年 3 月 Claude Code 曾出过一个 session-clearing 的 bug，清空了用户 memory。
`hypha guard` 存在的理由就是——**连官方 agent 都会弄丢状态**。不要信任任何 `git diff` 不出来的东西。

## 致谢

Hypha 站在以下工作的肩膀上：

- [**ACE** (Zhang et al., 2025)](https://arxiv.org/abs/2510.04618) — grow-and-refine playbook
- [**Mem0**](https://github.com/mem0ai/mem0) — A.U.D.N. 记忆操作（我们用更保守的子集）
- [**Reflexion** (Shinn et al., 2023)](https://arxiv.org/abs/2303.11366) — 自然语言自我反思
- [**Agent-R** (ByteDance, 2025)](https://arxiv.org/abs/2501.11425) — trajectory verifier
- [**Voyager** (Wang et al., 2023)](https://voyager.minedojo.org) — skill library
- [**DGM** (Sakana AI, 2025)](https://sakana.ai/dgm) — 适应度函数守门
- [**dream-skill**](https://github.com/grandamenium/dream-skill) — 社区对 Anthropic Auto Dream 的复刻
- [**Anthropic Agent Skills**](https://anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills) — 开放的 folder-of-instructions 标准
- [**agents.md**](https://agents.md) — 跨 agent 的 AGENTS.md 约定

## License

MIT © 2026 [XJM-free](https://github.com/XJM-free)

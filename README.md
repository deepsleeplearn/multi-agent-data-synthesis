# 多智能体美的空气能热水机客服对话数据生成框架

这个项目用于批量生成“美的集团空气能热水机/空气能热水器”客服场景的中文通话对话数据，当前先落地一个最小但可扩展的框架：

- `user_agent` 扮演真实用户，基于角色、产品和诉求与客服通话
- `service_agent` 扮演客服，逐步收集故障/安装描述、姓氏、电话、地址、型号等槽位
- `orchestrator` 负责轮次控制、槽位合并、结束条件判断和样本导出
- `scenario_factory` 负责加载和扩展场景，以支持批量生成
- `HiddenSettingsTool` 负责调用 LLM 为 `user_agent` 生成随机隐藏设定，并写入 JSONL 历史库做去重

当前领域限制是硬约束：

- 品牌只能是 `美的`
- 品类只能是 `空气能热水器` 或 `空气能热水机`
- 不符合约束的场景在加载阶段会直接报错

## 目录结构

```text
multi_agent_data_synthesis/
  config.py
  llm.py
  schemas.py
  prompts.py
  agents.py
  orchestrator.py
  scenario_factory.py
  validator.py
  exporter.py
  cli.py
  hidden_settings_tool.py
data/
  seed_scenarios.json
```

## 核心设计

参考 `learn-claude-code` 的思路，这里把重点放在 harness，而不是写死流程图：

- 模型层统一走 OpenAI 协议
- 两个 agent 各自维护自己的 system prompt 和可见上下文
- 隐藏设定工具会读取持久化 JSONL 历史，计算重复率和相似度，规避高重复样本
- 对话主循环稳定，后续可以继续加：
  - 场景生成 agent
  - 质检 agent
  - 改写 agent
  - 多客服角色协同

## 使用方式

1. 安装依赖

```bash
pip install -r requirements.txt
```

2. 配置环境变量

把 `.env.example` 复制为 `.env`，填入你的 OpenAI-compatible 接口：

```env
OPENAI_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=qwen-plus
SERVICE_OK_PREFIX_PROBABILITY=0.7
MAX_CONCURRENCY=5
```

- `SERVICE_OK_PREFIX_PROBABILITY`: 客服固定话术前带 `好的，` 的概率，`0` 表示从不带，`1` 表示总是带
- `MAX_CONCURRENCY`: 按场景异步并发调用模型的默认并发数

3. 生成数据

```bash
python -m multi_agent_data_synthesis.cli generate --count 10 --auto-hidden-settings --concurrency 5
```

输出文件：

- `outputs/dialogues.jsonl`
- `outputs/dialogues.json`

其中 `dialogues.jsonl` 的每一行都会包含：

- `dialogue_process`: 结构化对话轮次列表
- `dialogue_text`: 拼接后的完整对话文本
- `related_info`: 对应产品信息、用户隐藏设定、诉求、槽位收集结果和校验结果

如果你只想先批量生成隐藏设定，不跑对话：

```bash
python -m multi_agent_data_synthesis.cli generate-hidden-settings --count 10 --concurrency 5
```

隐藏设定历史会持久化到 `data/hidden_settings_history.jsonl`，后续生成会读取该文件并计算：

- `duplicate_rate`: 结构化字段逐项完全相同的比例
- `max_similarity_score`: 基于文本 n-gram Jaccard 的整体相似度

只要候选设定超过阈值，就会自动拒绝并重试。

如果希望在生成时直接看到用户和客服的逐轮交互过程，可以加：

```bash
python -m multi_agent_data_synthesis.cli generate --count 1 --auto-hidden-settings --show-dialogue
```

当前并发说明：

- 项目已经支持按 `scenario` 级别异步并发调用模型
- 单条对话内部仍按轮次串行推进，因为每一轮都依赖上一轮 transcript
- 开启 `--auto-hidden-settings` 时，隐藏设定历史库会在写入阶段串行校验，避免并发下去重失效

## 场景格式

`data/seed_scenarios.json` 中每个场景包含：

- `product`: 家电品牌、品类、型号、购买渠道
- `customer`: 用户姓名、姓氏、电话、地址、画像
- `request`: 诉求类型、问题描述、期望结果、可预约时间
- `required_slots`: 客服必须收集到的字段

其中 `product.brand` 必须为 `美的`，`product.category` 必须为 `空气能热水器` 或 `空气能热水机`。

## 下一步建议

这个版本是骨架，后续最值得继续补的能力是：

1. 增加场景自动采样器，从产品池和故障模板自动组合新样本
2. 增加质检 agent，剔除槽位缺失、语气不自然、信息泄露的样本
3. 增加标签体系，例如情绪、难度、一次解决/二次预约
4. 增加多轮改写，提升数据多样性

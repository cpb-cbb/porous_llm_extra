# 项目结构概览

> 本文档基于 2025-10-02 仓库状态整理，用于快速理解 `porous_llm_extra` 的模块划分与调用流程。

## 顶层入口

- `main.py`：面向命令行的示例入口，读取指定 JSON 文献并触发抽取流程。
- `run_workflow.py`：历史入口，直接导入各个 Agent，但未封装可执行函数。

## 核心模块划分

```
porous_llm_extra/
├── core/
│   └── config.py          # Pydantic Settings 占位，待扩展
├── servers/
│   ├── work_flows/
│   │   └── extract_por_super.py   # 主工作流，调度多个 Agent 并汇总结果
│   ├── agents/           # 单个职责的 LLM Agent（预判、性能、结构等）
│   └── utils/            # 通用工具（文本处理、Prompt、结果合并）
├── porous_carbon_info_extra/ # 旧版脚本与数据转换工具
└── datas/                # 静态数据、中间产物
```

### 工作流 (`servers/work_flows/extract_por_super.py`)

1. `prejudge` Agent 先判定文献是否相关，并抽取样本名。
2. 针对提取出的 `name_list` 构造复合输入文本。
3. 顺序调用三个信息抽取 Agent：
   - `process_extra`: 工艺流程
   - `micro_feature_extra`: 孔结构 & 物性
   - `ele_chem_extra`: 电化学性能
4. 每个 Agent 的返回结果再经过 `Validation_Agent` 验证（若为 `process_extra`）。
5. `merge_agent_outputs_simple` 负责将多路结果按样本名合并成统一结构。

### Agent 层 (`servers/agents/*`)

- 通过 `BaseZhipuAgent` 共享 GLM 请求、重试与错误处理逻辑，并集中读取 `core.config.settings` 中的统一配置。
- 各具体 Agent 仅关注 Prompt 构造与解析器（如 `json_repair.loads`）。

### 工具层 (`servers/utils/*`)

- `TextProcess.TextProcessor`: 负责 PDF / JSON / JSONL 读取与清洗。
- `prompts_en.py`: 统一管理英文 Prompt 文本。
- `tools.py`: 提供面向工作流的合并函数。

### 旧版/附加脚本

- `porous_carbon_info_extra/`: 包含批量调用、CSV 转换等脚本，与当前工作流耦合较弱。
- `datas/`: 存放实验数据与输出示例。

## 数据流总结

```
文献 JSON → TextProcessor.read_json → 文本 (str)
    ↓
prejudge → 样本列表
    ↓
loop_extract("process") → 验证 Agent → JSON
loop_extract("micro")   → JSON
loop_extract("ele")     → JSON
    ↓
merge_agent_outputs_simple → 统一结果
    ↓
写入目标 JSON 文件
```

## 改进线索（概要）

- 抽取 Agent 之间存在大量重复逻辑，可抽象成复用的 BaseAgent。
- `core/config.py` 仅初始化 Settings，可纳入 API Key、路径等集中管理。
- 建议拆分 `TextProcessor` 为更小的 I/O 组件，并补充异常处理和单元测试。
- 当前仓库同时包含 `servers` 与 `porous_carbon_info_extra` 两套脚本，可考虑归档或模块化以减少混淆。

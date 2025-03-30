# ReasoningAgent 文档

## 简介

ReasoningAgent是一个高级推理系统，它不仅超越了简单的思维链(Chain of Thought, CoT)方法，还支持多种推理策略并能使用工具执行操作。它基于ReActAgent（思考-行动代理）设计，提供了显式、结构化的推理过程，使用标签来跟踪和分析推理过程，然后能够执行具体行动。

## 支持的推理策略

ReasoningAgent支持以下策略：

| 策略 | ID | 描述 | 最适合 |
|----------|-------|-------------|----------|
| 思维链 | `chain_of_thought` | 线性逐步推理 | 一般问题解决、数学问题 |
| 思维树 | `tree_of_thought` | 探索多条推理路径 | 有多个选项的复杂决策 |
| 苏格拉底式提问 | `socratic` | 使用探究性问题探索话题 | 深入探索概念、哲学话题 |
| 第一原理 | `first_principles` | 分解到基本真理 | 复杂系统、工程问题 |
| 类比推理 | `analogical` | 使用类比理解问题 | 与已知领域相似的新问题 |
| 反事实推理 | `counterfactual` | 探索"如果"场景 | 因果推理、风险评估 |
| 退一步思考 | `step_back` | 采取更广泛的视角 | 需要上下文/高层次视角的问题 |

## 基本用法

### 简单单策略示例

```python
from app.agent import ReasoningAgent, ReasoningStrategy

# 使用思维链策略创建代理
agent = ReasoningAgent(primary_strategy=ReasoningStrategy.COT)

# 运行一个问题
result = await agent.run("减少碳排放的最有效方法是什么？")
```

### 多策略示例

```python
from app.agent import ReasoningAgent, ReasoningStrategy

# 创建具有多种策略的代理
agent = ReasoningAgent(
    primary_strategy=ReasoningStrategy.FIRST_PRINCIPLES,
    fallback_strategies=[ReasoningStrategy.COUNTERFACTUAL, ReasoningStrategy.STEP_BACK],
    max_steps=3  # 允许最多3个推理步骤
)

# 运行一个问题
result = await agent.run("人工通用智能对社会的影响是什么？")
```

### 使用工具进行推理和行动

```python
from app.agent import ReasoningAgent, ReasoningStrategy
from app.tool import Python, WebSearch, ToolCollection

# 创建具有工具能力的推理代理
agent = ReasoningAgent(
    primary_strategy=ReasoningStrategy.FIRST_PRINCIPLES,
    available_tools=ToolCollection(
        Python(),      # 执行Python代码
        WebSearch()    # 搜索网络信息
    ),
    max_steps=8        # 允许更多步骤用于工具使用
)

# 运行一个需要推理和执行的任务
result = await agent.run("""
分析气候数据趋势的最佳方法是什么？请在推理完成后，
帮我实现一个使用matplotlib可视化温度变化的简单Python脚本。
""")

# 用户确认进行行动
result = await agent.run("是的，请帮我实现这个解决方案。")
```

## 推理设置

您可以自定义推理过程的各个方面：

```python
agent = ReasoningAgent(
    # 策略配置
    primary_strategy=ReasoningStrategy.TOT,
    fallback_strategies=[ReasoningStrategy.ANALOGICAL],

    # 推理深度/广度设置
    max_reasoning_depth=4,  # 树状推理的最大深度
    exploration_breadth=3,  # 树/图探索策略的宽度
    min_alternatives=3,     # 考虑的最少替代路径

    # 工具配置
    available_tools=ToolCollection(...),  # 添加可用工具

    # 整体执行设置
    max_steps=5  # 最大步骤数
)
```

## 理解输出

代理产生的结构化输出使用XML标签标记推理过程的不同部分：

```xml
<reasoning>
  <question>重述问题...</question>
  <strategy>策略名称</strategy>
  <process>
    详细推理过程...
  </process>
  <alternatives>
    替代方法...
  </alternatives>
  <evaluation>
    优缺点评估...
  </evaluation>
  <conclusion>
    最终答案...
  </conclusion>
</reasoning>
```

不同策略在`<process>`部分内可能有额外的专门标签。

## 分析推理过程

代理在`reasoning_trace`属性中跟踪推理过程：

```python
agent = ReasoningAgent()
await agent.run("您的问题")

# 分析推理轨迹
for step in agent.reasoning_trace:
    print(f"步骤 {step['step']}")
    print(f"使用的策略: {step['strategies_used']}")
    print(f"存在的组件: {step['components']}")
    print(f"推理深度: {step['depth']}")
    print()
```

## 工具使用能力

ReasoningAgent基于ReActAgent实现，因此具有强大的工具使用能力。它采用两阶段方法：

1. **推理阶段**：代理首先使用选定的推理策略分析问题，完成全部结构化思考过程
2. **行动阶段**：推理完成后，代理询问用户是否想执行具体操作
3. **交互方式**：用户可以确认执行操作（回复"yes"、"好的"等），也可以提供更具体的指示

工作流程：

1. 用户提供问题或任务
2. 代理使用适当的推理策略进行深入分析
3. 代理完成推理并询问用户是否要采取行动
4. 用户确认后，代理准备执行所需操作
5. 代理可以使用各种工具来实施解决方案

可用工具示例：

- **Python**：执行Python代码以实现解决方案
- **FileRead/FileWrite**：读写文件
- **WebSearch**：搜索网络获取信息
- **自定义工具**：可以添加任何其他工具

## 选择正确的策略

不同的推理策略适合不同类型的问题：

- **思维链**：适合需要逻辑递进的直接问题
- **思维树**：适合有多种可能方法的问题
- **第一原理**：适合复杂系统的基本分析
- **苏格拉底式**：适合概念和信念的深入探索
- **类比推理**：适合有类似领域参照的新问题
- **反事实推理**：适合因果推理和理解依赖关系
- **退一步思考**：适合需要更广泛上下文的问题

## 运行示例

要查看ReasoningAgent的运行情况，运行示例脚本：

```bash
python examples/reasoning_agent_example.py
```

这将让您尝试不同的推理策略并查看它们如何处理相同的问题，以及如何使用工具执行操作。新版本的示例还包括交互式会话，让您可以体验完整的推理-行动流程。

## 自定义提示

如果您想自定义用于每种推理策略的提示，可以修改`app/prompt/reasoning.py`中的模板。

## 与ReActAgent的关系

ReasoningAgent直接继承自ReActAgent，这意味着它具备了ReAct框架的强大基础：

1. **思考-行动循环**：遵循思考(Think)和行动(Act)的核心循环
2. **原生工具支持**：能够与各种工具自然集成
3. **结构化处理**：能够以结构化方式处理复杂任务

与标准ReActAgent的区别在于，ReasoningAgent添加了：

1. 多种专门的推理策略
2. 结构化的XML标记输出
3. 两阶段处理（先推理，后行动）
4. 推理轨迹分析和跟踪

## 最佳实践

1. **匹配策略与问题**：不同问题受益于不同的推理方法
2. **对复杂问题使用多策略**：结合策略可以提供更健全的推理
3. **检查推理轨迹**：查看使用了哪些组件以了解过程
4. **调整深度设置**：更复杂的问题可能需要更大的探索深度
5. **对多步推理使用步骤指导**：对于复杂问题，将它们分解为多个步骤
6. **分离推理和行动**：允许代理先完成所有推理，然后执行操作
7. **明确确认行动**：在代理采取行动前，确保用户明确确认

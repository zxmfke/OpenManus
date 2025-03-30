# Advanced Reasoning Agent with Multiple Reasoning Strategies and Tool Usage

## Overview

This PR implements a sophisticated `ReasoningAgent` that extends beyond the basic Chain of Thought (CoT) approach to support multiple reasoning strategies with explicit, XML-tagged structures. Unlike basic CoT which is already an inherent capability of most LLMs, this implementation is based on the ReActAgent framework for natively supporting tool usage, while providing a structured reasoning phase before taking actions.

## Key Features

### 1. Multiple Reasoning Strategies

The implementation supports seven different reasoning strategies:

- **Chain of Thought (CoT)**: Step-by-step linear reasoning
- **Tree of Thought (ToT)**: Exploring multiple reasoning paths
- **Socratic Questioning**: Using probing questions to explore the topic
- **First Principles Reasoning**: Breaking down to fundamental truths
- **Analogical Reasoning**: Using analogies to understand the problem
- **Counterfactual Reasoning**: Exploring "what if" scenarios
- **Step-Back Reasoning**: Taking a broader perspective before diving into details

### 2. Structured XML-Tagged Output

Each reasoning process is structured with XML tags to clearly mark different components:

```xml
<reasoning>
  <question>Problem restatement</question>
  <strategy>strategy_name</strategy>
  <process>Detailed reasoning process</process>
  <alternatives>Alternative approaches</alternatives>
  <evaluation>Strengths and weaknesses</evaluation>
  <conclusion>Final answer</conclusion>
</reasoning>
```

### 3. Multi-Strategy Reasoning

The agent can combine multiple strategies, with:

- A primary strategy that guides the main reasoning approach
- Fallback strategies for additional perspectives
- Dynamic strategy selection based on the problem

### 4. Advanced Reasoning Analysis

The agent includes a reasoning trace system that:

- Tracks which strategies are used in each step
- Monitors which reasoning components are present
- Provides analytics on the reasoning process

### 5. Multi-Step Reasoning

The implementation supports complex multi-step reasoning, with:

- Configurable maximum reasoning depth
- Strategy-specific guidance for each step
- Automated reasoning completion detection

### 6. ReAct Integration (Think-Act Capability)

The agent extends ReActAgent for native tool integration:

- Two-phase approach: reasoning phase followed by action phase
- Inherits from ReActAgent for direct access to tool execution framework
- Clear separation between reasoning and tool-based action
- Interactive confirmation before proceeding with actions
- Structured mechanism for transitioning from reasoning to action

## Implementation Details

### New Files

- `app/agent/reasoning.py`: Main ReasoningAgent implementation
- `app/prompt/reasoning.py`: Strategy-specific prompt templates
- `examples/reasoning_agent_example.py`: Example showcasing different strategies and tool usage

### Changes to Existing Files

- Updated `app/agent/__init__.py` to include the new agent
- Modified `select_agent.py` to include the ReasoningAgent as an option

## Usage Example

```python
from app.agent import ReasoningAgent, ReasoningStrategy

# Simple single-strategy usage
agent = ReasoningAgent(primary_strategy=ReasoningStrategy.TOT)
result = await agent.run("What are the ethical implications of AGI?")

# Multi-strategy usage
agent = ReasoningAgent(
    primary_strategy=ReasoningStrategy.COT,
    fallback_strategies=[ReasoningStrategy.COUNTERFACTUAL, ReasoningStrategy.STEP_BACK],
    max_steps=3
)
result = await agent.run("What are the most effective strategies to address climate change?")

# Reasoning with tool usage (two-step process)
from app.tool import Python, WebSearch, ToolCollection

agent = ReasoningAgent(
    primary_strategy=ReasoningStrategy.FIRST_PRINCIPLES,
    available_tools=ToolCollection(
        Python(),
        WebSearch()
    ),
    max_steps=8
)
# First run for reasoning phase
result = await agent.run("Analyze optimal solar panel placement and create a simulation script.")
# Second run for action phase (after user confirmation)
result = await agent.run("Yes, please implement the solution.")
```

## How This Differs From Basic CoT

1. **Structure**: Enforces explicit reasoning structure with XML tags
2. **Strategy Variety**: Goes beyond linear CoT to support branching, counterfactual, and other reasoning patterns
3. **Transparency**: Makes the reasoning strategy explicit rather than implicit
4. **Customizability**: Allows selection of specific reasoning strategies for different problem types
5. **Analysis**: Provides meta-analysis of the reasoning process itself
6. **Two-Phase Approach**: Clear separation of reasoning phase and action phase
7. **ReAct Foundation**: Built on the ReAct (Reasoning+Acting) paradigm for tool usage

## Testing

The implementation has been tested with various reasoning scenarios. The example script demonstrates each strategy individually, multi-strategy combinations, and integration with tools through the ReAct framework.

## Future Improvements

- Add XML validation to ensure proper tag structure
- Implement strategy recommendation based on question type
- Add support for reasoning with external knowledge bases
- Develop visualization tools for reasoning trees
- Allow for dynamic strategy switching during reasoning
- Add automated reasoning evaluation metrics

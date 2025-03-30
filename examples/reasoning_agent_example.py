#!/usr/bin/env python3
"""
ReasoningAgent Example - Demonstrates advanced reasoning with multiple strategies and tool usage
"""

import asyncio
import sys
from pathlib import Path

# Add project root directory to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.agent.reasoning import ReasoningAgent, ReasoningStrategy
from app.logger import logger
from app.tool import PythonExecute, StrReplaceEditor, WebSearch, ToolCollection


async def single_strategy_example(strategy: ReasoningStrategy, question: str):
    """Run an example with a single reasoning strategy"""
    agent = ReasoningAgent(
        name=f"{strategy.value}_agent",
        primary_strategy=strategy,
        max_steps=4  # Limit to 4 steps for example purposes
    )

    logger.info(f"Starting {strategy.value} reasoning example")
    logger.info(f"Question: {question}")

    result = await agent.run(question)

    logger.info(f"{strategy.value} reasoning complete!")
    return result


async def multi_strategy_example(question: str):
    """Run an example with multiple reasoning strategies"""
    agent = ReasoningAgent(
        name="multi_strategy_agent",
        primary_strategy=ReasoningStrategy.COT,
        fallback_strategies=[ReasoningStrategy.TOT, ReasoningStrategy.COUNTERFACTUAL],
        max_steps=5  # Allow up to 5 steps for multi-strategy reasoning
    )

    logger.info("Starting multi-strategy reasoning example")
    logger.info(f"Question: {question}")

    result = await agent.run(question)

    logger.info("Multi-strategy reasoning complete!")
    return result


async def tool_usage_example():
    """Run an example showcasing tool usage with reasoning"""
    # Create a ReasoningAgent with tools
    agent = ReasoningAgent(
        name="reasoning_with_tools",
        primary_strategy=ReasoningStrategy.FIRST_PRINCIPLES,
        # Add useful tools for research and implementation
        available_tools=ToolCollection(
            PythonExecute(),    # Execute Python code
            StrReplaceEditor(), # File operations (read/write)
            WebSearch(),        # Search the web
        ),
        max_steps=8  # Allow more steps for tool usage
    )

    # Example task requiring reasoning and tool use
    task = """
    I need to analyze climate data trends. First reason through the best approach,
    and then help me implement a small Python script that visualizes temperature
    changes over time using matplotlib.
    """

    logger.info("Starting reasoning agent with tool usage example")
    logger.info(f"Task: {task}")

    # First run for reasoning phase
    result = await agent.run(task)

    # For demonstration, simulate user response to use tools
    logger.info("User confirms to proceed with actions")
    result = await agent.run("Yes, please help me implement the solution.")

    logger.info("Reasoning with tools example complete!")
    return result


async def interactive_example():
    """Run an interactive example with the ReasoningAgent"""
    # Setup agent
    agent = ReasoningAgent(
        name="interactive_agent",
        primary_strategy=ReasoningStrategy.FIRST_PRINCIPLES,
        fallback_strategies=[ReasoningStrategy.STEP_BACK],
        available_tools=ToolCollection(
            PythonExecute(),
            WebSearch()
        ),
        max_steps=10
    )

    # Initial prompt
    question = input("\nEnter your question or task: ")
    if not question.strip():
        question = "What are the most effective strategies to combat climate change?"

    print("\nAgent is reasoning...")
    result = await agent.run(question)
    print(f"\nInitial reasoning complete. Result:\n{result}")

    # Ask if user wants to proceed with actions
    user_action = input("\nDo you want the agent to take any actions based on its reasoning? (yes/no): ")

    if user_action.lower() in ["yes", "y", "sure", "ok"]:
        print("\nAgent is taking action...")
        action_result = await agent.run(user_action)
        print(f"\nAction result:\n{action_result}")

    # Allow follow-up conversation
    while True:
        next_input = input("\nEnter your next instruction (or 'exit' to quit): ")
        if next_input.lower() in ["exit", "quit", "q"]:
            break

        print("\nAgent is processing...")
        response = await agent.run(next_input)
        print(f"\nResponse:\n{response}")

    return "Interactive session complete"


async def custom_strategy_example():
    """Run a customized example based on user input"""
    # List available strategies
    print("Available reasoning strategies:")
    for i, strategy in enumerate(ReasoningStrategy):
        print(f"{i+1}. {strategy.name}: {strategy.value.replace('_', ' ').title()}")

    # Get user selection
    try:
        selection = int(input("\nSelect primary strategy (1-7): "))
        if selection < 1 or selection > 7:
            raise ValueError("Invalid selection")

        primary = list(ReasoningStrategy)[selection-1]

        # Get optional fallback strategies
        use_fallbacks = input("Add fallback strategies? (y/n): ").lower() == "y"
        fallbacks = []

        if use_fallbacks:
            fallback_input = input("Enter fallback strategy numbers (e.g., '2 5'): ")
            fallback_indices = [int(idx) - 1 for idx in fallback_input.split()]
            fallbacks = [list(ReasoningStrategy)[idx] for idx in fallback_indices
                        if 0 <= idx < len(ReasoningStrategy)]

        # Ask if tools should be added
        use_tools = input("Add tools for the agent to use? (y/n): ").lower() == "y"
        tools = ToolCollection()

        if use_tools:
            print("\nAvailable tools:")
            print("1. Python (execute code)")
            print("2. File Operations (read/write)")
            print("3. WebSearch (search the web)")
            print("4. All tools")

            tool_choice = input("Select tools (e.g., '1 3' or '4' for all): ")

            if "1" in tool_choice or "4" in tool_choice:
                tools.add(PythonExecute())
            if "2" in tool_choice or "4" in tool_choice:
                tools.add(StrReplaceEditor())
            if "3" in tool_choice or "4" in tool_choice:
                tools.add(WebSearch())

        # Get question
        question = input("\nEnter your question/task: ")
        if not question.strip():
            question = "What are the ethical implications of artificial general intelligence?"

        # Create and run agent
        agent = ReasoningAgent(
            name="custom_agent",
            primary_strategy=primary,
            fallback_strategies=fallbacks,
            available_tools=tools if use_tools else None,
            max_steps=6
        )

        logger.info(f"Starting custom reasoning with {primary.value} as primary strategy")
        if fallbacks:
            logger.info(f"Fallback strategies: {', '.join(s.value for s in fallbacks)}")
        if use_tools:
            logger.info(f"Tools enabled: {[t.name for t in tools.tools]}")
        logger.info(f"Question: {question}")

        # Initial reasoning phase
        result = await agent.run(question)
        logger.info("Initial reasoning complete!")

        # If tools are enabled, ask if user wants to proceed
        if use_tools and tools.tools:
            proceed = input("\nWould you like to proceed with actions? (y/n): ").lower() == "y"
            if proceed:
                action_result = await agent.run("Yes, proceed with actions")
                logger.info("Action phase complete!")
                return action_result

        return result

    except (ValueError, IndexError) as e:
        logger.error(f"Error in selection: {e}")
        print("Using default strategies instead")
        return await multi_strategy_example("What are the ethical implications of artificial general intelligence?")


async def main():
    choice = input("""
Select an example to run:
1. Chain of Thought (CoT) reasoning
2. Tree of Thought (ToT) reasoning
3. First Principles reasoning
4. Multiple strategies combined
5. Reasoning with tool usage
6. Interactive session
7. Custom reasoning (select your own)

Enter choice (1-7): """)

    # Default question for examples
    question = "What are the most effective strategies to address climate change?"

    if choice == "1":
        await single_strategy_example(ReasoningStrategy.COT, question)
    elif choice == "2":
        await single_strategy_example(ReasoningStrategy.TOT, question)
    elif choice == "3":
        await single_strategy_example(ReasoningStrategy.FIRST_PRINCIPLES, question)
    elif choice == "4":
        await multi_strategy_example(question)
    elif choice == "5":
        await tool_usage_example()
    elif choice == "6":
        await interactive_example()
    elif choice == "7":
        await custom_strategy_example()
    else:
        print("Invalid choice. Running Chain of Thought example.")
        await single_strategy_example(ReasoningStrategy.COT, question)


if __name__ == "__main__":
    asyncio.run(main())

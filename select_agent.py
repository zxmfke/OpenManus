#!/usr/bin/env python3
"""
Agent Selector - Allows users to choose different agent modes
"""

import asyncio
import sys
from typing import List, Optional

from app.agent import CoTAgent, ReasoningAgent, ReasoningStrategy
from app.agent.manus import Manus
from app.logger import logger


async def run_cot_agent():
    """Run Chain of Thought agent"""
    agent = CoTAgent()
    prompt = input("Enter your question: ")
    if not prompt.strip():
        logger.warning("Empty question provided")
        return

    logger.warning("Processing your question...")
    result = await agent.run(prompt)
    logger.info("Question processing completed")


async def run_react_agent():
    """Run ReAct agent (Manus)"""
    agent = Manus()
    prompt = input("Enter your request: ")
    if not prompt.strip():
        logger.warning("Empty request provided")
        return

    logger.warning("Processing your request...")
    await agent.run(prompt)
    logger.info("Request processing completed")


async def run_reasoning_agent():
    """Run advanced Reasoning agent with multiple strategies"""
    # Display available strategies
    print("\nAvailable reasoning strategies:")
    for i, strategy in enumerate(ReasoningStrategy):
        strategy_name = strategy.value.replace("_", " ").title()
        print(f"{i+1}. {strategy_name}")

    # Get primary strategy
    primary_idx = int(input("\nSelect primary strategy (1-7) [default=1]: ") or "1")
    primary_idx = max(1, min(7, primary_idx)) - 1  # Clamp between 0-6
    primary = list(ReasoningStrategy)[primary_idx]

    # Get optional fallback strategies
    fallbacks: List[ReasoningStrategy] = []
    use_fallbacks = input("Add fallback strategies? (y/n) [default=n]: ").lower()

    if use_fallbacks == "y":
        fallback_input = input("Enter fallback strategy numbers separated by space (e.g., '2 5'): ")
        try:
            fallback_indices = [int(idx) - 1 for idx in fallback_input.split()]
            fallbacks = [list(ReasoningStrategy)[idx] for idx in fallback_indices
                        if 0 <= idx < len(ReasoningStrategy) and idx != primary_idx]
        except (ValueError, IndexError):
            print("Invalid fallback selection. Proceeding with primary strategy only.")

    # Get question
    question = input("\nEnter your question: ")
    if not question.strip():
        logger.warning("Empty question provided")
        return

    # Create and run agent
    agent = ReasoningAgent(
        primary_strategy=primary,
        fallback_strategies=fallbacks,
        max_steps=3  # Limit to 3 steps for interactive use
    )

    logger.warning(f"Processing with {primary.value} reasoning strategy...")
    if fallbacks:
        fallback_names = [s.value.replace("_", " ").title() for s in fallbacks]
        logger.info(f"Using fallback strategies: {', '.join(fallback_names)}")

    result = await agent.run(question)
    logger.info("Reasoning completed")


async def main():
    print("\nSelect the agent mode to use:")
    print("1. ReAct mode - Can use tools to execute tasks")
    print("2. Basic Chain of Thought (CoT) mode - Simple step-by-step thinking")
    print("3. Advanced Reasoning mode - Multiple reasoning strategies with structured output")

    choice = input("\nEnter option (1-3): ").strip()

    try:
        if choice == "1":
            await run_react_agent()
        elif choice == "2":
            await run_cot_agent()
        elif choice == "3":
            await run_reasoning_agent()
        else:
            print("Invalid choice, please enter a number between 1-3")
    except Exception as e:
        logger.error(f"Error during agent execution: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.warning("Operation interrupted")
        sys.exit(0)

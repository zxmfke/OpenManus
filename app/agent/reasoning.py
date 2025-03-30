from enum import Enum
from typing import Dict, List, Optional, Set, Union

from pydantic import Field, field_validator

from app.agent.react import ReActAgent
from app.llm import LLM
from app.logger import logger
from app.prompt.reasoning import STRATEGY_PROMPTS, MULTI_STRATEGY_PROMPT
from app.schema import AgentState, Message
from app.tool import CreateChatCompletion, Terminate, ToolCollection


class ReasoningStrategy(str, Enum):
    """Enumeration of supported reasoning strategies."""
    COT = "chain_of_thought"  # Chain of Thought
    TOT = "tree_of_thought"   # Tree of Thought
    SOCRATIC = "socratic"     # Socratic questioning
    FIRST_PRINCIPLES = "first_principles"  # First principles reasoning
    ANALOGICAL = "analogical"  # Analogical reasoning
    COUNTERFACTUAL = "counterfactual"  # Counterfactual reasoning
    STEP_BACK = "step_back"   # Step-back reasoning


class ReasoningAgent(ReActAgent):
    """
    Advanced reasoning agent supporting multiple reasoning strategies with tool capabilities.

    This agent extends ReActAgent with sophisticated reasoning methods,
    allowing for transparent and structured thinking processes with
    XML/tag-based formatting to clearly mark different reasoning phases,
    while also being able to use tools to act on the environment.
    """

    name: str = "reasoning"
    description: str = "An advanced agent that employs multiple reasoning strategies and can use tools"

    # Reasoning-specific configuration
    primary_strategy: ReasoningStrategy = ReasoningStrategy.COT
    fallback_strategies: List[ReasoningStrategy] = Field(default_factory=list)
    active_strategies: Set[ReasoningStrategy] = Field(default_factory=set)

    # Reasoning settings
    max_reasoning_depth: int = 3  # Maximum depth for tree-based reasoning
    exploration_breadth: int = 2  # For tree/graph exploration strategies
    min_alternatives: int = 2     # Minimum alternative paths to consider

    # Tracking and analysis
    reasoning_trace: List[Dict] = Field(default_factory=list)
    reasoning_complete: bool = False

    # Default tools
    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            CreateChatCompletion(), Terminate()
        )
    )

    # LLM configuration
    llm: LLM = Field(default_factory=LLM)
    max_steps: int = 10  # Default max steps for complex reasoning

    # Reasoning phases
    in_reasoning_phase: bool = True
    current_reasoning_step: int = 0

    # State tracking
    _current_result: str = ""

    @field_validator('fallback_strategies')
    def ensure_unique_strategies(cls, v, values):
        """Ensure primary strategy is not duplicated in fallback strategies"""
        if 'primary_strategy' in values and values['primary_strategy'] in v:
            v.remove(values['primary_strategy'])
        return v

    async def initialize_reasoning(self) -> None:
        """Initialize the reasoning session based on selected strategies"""
        self.active_strategies = {self.primary_strategy}
        self.active_strategies.update(self.fallback_strategies[:2])  # Add up to 2 fallback strategies
        self.reasoning_trace = []
        self.in_reasoning_phase = True
        self.current_reasoning_step = 0
        self.reasoning_complete = False

        strategy_names = [s.value for s in self.active_strategies]
        logger.info(f"🧠 Initializing {self.name} with strategies: {', '.join(strategy_names)}")

    def _get_system_prompt(self) -> str:
        """Generate appropriate system prompt based on active reasoning strategies"""
        # If only one strategy is active, use its dedicated prompt
        if len(self.active_strategies) == 1:
            strategy_value = next(iter(self.active_strategies)).value
            return STRATEGY_PROMPTS.get(strategy_value, "")

        # If multiple strategies are active, use the multi-strategy prompt
        primary_strategy = self.primary_strategy.value.replace('_', ' ').title()
        additional_strategies = [s.value.replace('_', ' ').title()
                                for s in self.active_strategies
                                if s != self.primary_strategy]

        additional_str = ", ".join(additional_strategies)
        return MULTI_STRATEGY_PROMPT.format(
            primary_strategy=primary_strategy,
            additional_strategies=additional_str
        )

    async def think(self) -> bool:
        """Process current state and decide next actions"""
        # Initialize reasoning if this is the first step or if we haven't initialized yet
        if self.current_step == 1 or (self.in_reasoning_phase and self.current_reasoning_step == 0):
            await self.initialize_reasoning()

        # If we're in the reasoning phase, handle it differently
        if self.in_reasoning_phase:
            self.current_reasoning_step += 1

            # Generate reasoning-specific prompt
            system_prompt = self._get_system_prompt()

            # Add strategy-specific guidance for this step
            step_guidance = self._get_step_guidance()
            user_input = self.messages[-1].content if self.messages and self.messages[-1].role == "user" else ""

            if step_guidance:
                user_input = f"{user_input}\n\n{step_guidance}" if user_input else step_guidance
                if self.messages and self.messages[-1].role == "user":
                    # Update the last user message instead of adding a new one
                    self.memory.messages[-1] = Message.user_message(user_input)
                else:
                    self.memory.add_message(Message.user_message(user_input))

            # Get response from LLM with structured reasoning
            response = await self.llm.ask(
                messages=self.messages,
                system_msgs=[Message.system_message(system_prompt)],
            )

            # Record assistant's response
            self.memory.add_message(Message.assistant_message(response))

            # Extract and analyze reasoning structure
            self._analyze_reasoning(response)

            # Determine if reasoning is complete
            if self._is_reasoning_complete(response):
                self.reasoning_complete = True
                self.in_reasoning_phase = False
                logger.info(f"🧠 {self.name} reasoning phase complete after {self.current_reasoning_step} steps")

                # Ask if the user wants to take actions based on the reasoning
                action_prompt = "Based on my reasoning above, would you like me to take any actions? I can use tools to help implement any solutions or gather more information."
                self.memory.add_message(Message.assistant_message(action_prompt))

                # Store the reasoning result for later use
                self._current_result = response

                return False  # No action needed yet, wait for user response

            return False  # Continue in reasoning phase, no action needed yet

        # If reasoning is complete, proceed with normal ReAct think process
        # This is where we check if there's a go-ahead from the user to act
        user_last_message = self.messages[-1].content.lower() if self.messages and self.messages[-1].role == "user" else ""

        affirmative_responses = ["yes", "sure", "ok", "okay", "go ahead", "proceed", "let's do it", "execute", "act"]
        should_act = any(resp in user_last_message for resp in affirmative_responses)

        if should_act:
            logger.info(f"🧠 {self.name} proceeding to act based on reasoning")
            return True

        # If no clear action direction, ask for clarification
        if self.current_step > 1 and self.reasoning_complete and not should_act:
            clarification_msg = "Would you like me to take any specific action based on my reasoning? Please respond with 'yes' if you want me to proceed with actions."
            self.memory.add_message(Message.assistant_message(clarification_msg))

        return False  # No clear action direction yet

    async def act(self) -> str:
        """Execute actions based on the reasoning"""
        # Default implementation - can be overridden in subclasses for specific action patterns
        logger.info(f"🧠 {self.name} executing actions based on reasoning")

        # Default action is to summarize the reasoning conclusions
        conclusion_start = self._current_result.lower().find("<conclusion>")
        conclusion_end = self._current_result.lower().find("</conclusion>")

        if conclusion_start >= 0 and conclusion_end > conclusion_start:
            conclusion = self._current_result[conclusion_start + 12:conclusion_end].strip()
            action_msg = f"Based on my reasoning, I will act on the following conclusion:\n\n{conclusion}\n\nWhat specific action would you like me to take?"
        else:
            action_msg = "I'm ready to act based on my reasoning. What specific action would you like me to take?"

        self.memory.add_message(Message.assistant_message(action_msg))
        return action_msg

    def _get_step_guidance(self) -> str:
        """Get strategy-specific guidance for the current reasoning step"""
        if self.current_reasoning_step == 1:
            return ""

        guidance = []

        # First check for strategy-specific guidance
        if ReasoningStrategy.TOT in self.active_strategies:
            if self.current_reasoning_step == 2:
                guidance.append("For this step, continue exploring the most promising branches from your initial reasoning.")
            elif self.current_reasoning_step == 3:
                guidance.append("For this step, select the most promising branch and develop it further.")

        if ReasoningStrategy.SOCRATIC in self.active_strategies:
            if self.current_reasoning_step == 2:
                guidance.append("For this step, deepen your inquiry with follow-up questions based on your initial exploration.")
            elif self.current_reasoning_step == 3:
                guidance.append("For this step, synthesize insights from your questioning process.")

        # For multiple strategies, add synthesis guidance
        if len(self.active_strategies) > 1 and self.current_reasoning_step >= 3:
            guidance.append("Begin synthesizing insights from the different reasoning strategies you've employed.")

        # For final steps, focus on conclusion
        if self.current_reasoning_step >= max(3, self.max_steps - 1):
            guidance.append("Focus on finalizing your conclusion based on all your reasoning so far.")

        return "\n".join(guidance)

    def _analyze_reasoning(self, response: str) -> None:
        """Analyze the reasoning structure in the response"""
        # Track strategies used in this step
        used_strategies = set()

        # Simple tag detection (in a production system, this would use proper XML parsing)
        strategies_to_check = [s.value for s in ReasoningStrategy]
        for strategy in strategies_to_check:
            if f"<strategy>{strategy}</strategy>" in response.lower():
                used_strategies.add(strategy)

        # Additional check for primary_strategy tag
        if "<primary_strategy>" in response.lower():
            for strategy in strategies_to_check:
                if f"<primary_strategy>{strategy}</primary_strategy>" in response.lower():
                    used_strategies.add(strategy)

        # Track reasoning components
        components = ["question", "process", "alternatives", "evaluation", "conclusion"]
        found_components = {c: f"<{c}>" in response.lower() and f"</{c}>" in response.lower()
                           for c in components}

        # Track advanced components based on strategies
        advanced_components = {}
        if ReasoningStrategy.TOT in self.active_strategies:
            advanced_components["branch"] = "<branch" in response.lower()
            advanced_components["branch_selection"] = "<branch_selection>" in response.lower()

        if ReasoningStrategy.COUNTERFACTUAL in self.active_strategies:
            advanced_components["counterfactual"] = "<counterfactual" in response.lower()

        if ReasoningStrategy.SOCRATIC in self.active_strategies:
            advanced_components["inquiry"] = "<inquiry>" in response.lower()

        # Record trace information for this step
        self.reasoning_trace.append({
            "step": self.current_reasoning_step,
            "strategies_used": list(used_strategies),
            "components": {**found_components, **advanced_components},
            "depth": sum([1 for c in found_components.values() if c])
        })

        logger.info(f"🧠 Reasoning analysis - Strategies used: {', '.join(used_strategies) or 'none detected'}")

    def _is_reasoning_complete(self, response: str) -> bool:
        """Determine if the reasoning process should be considered complete"""
        # Check if this is the last allowed step
        if self.current_reasoning_step >= self.max_steps:
            return True

        # Check for conclusion tag
        has_conclusion = "<conclusion>" in response.lower() and "</conclusion>" in response.lower()

        # For ToT reasoning, check if we've reached max depth
        if ReasoningStrategy.TOT in self.active_strategies and self.current_reasoning_step >= self.max_reasoning_depth:
            return has_conclusion

        # For single-step strategies, one comprehensive answer is enough
        if len(self.active_strategies) == 1 and self.primary_strategy == ReasoningStrategy.COT:
            return has_conclusion

        # For more complex strategies, require multiple steps
        return has_conclusion and self.current_reasoning_step >= 2

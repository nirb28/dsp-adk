"""
Skill Service for loading and applying skills to agents.
"""
import os
import logging
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from ..models.skills import (
    SkillConfig, 
    SkillInstance, 
    SkillApplicationMode,
    OrchestrationStep
)
from ..models.telemetry import ActionType, SpanStatus, SpanKind
from ..core.base import ComponentType
from .telemetry_service import get_telemetry_service

logger = logging.getLogger(__name__)


class SkillService:
    """
    Service for managing and applying skills to agents.
    
    Handles:
    - Loading skill configurations
    - Applying skills in different modes
    - Parameter substitution
    - Skill validation
    """
    
    def __init__(self, skills_dir: str = "data/skills"):
        """Initialize skill service with skills directory."""
        self.skills_dir = Path(skills_dir)
        self._skills_cache: Dict[str, SkillConfig] = {}
        self.telemetry_service = get_telemetry_service()
        self._load_skills()
    
    def _load_skills(self):
        """Load all skill configurations from the skills directory."""
        if not self.skills_dir.exists():
            logger.warning(f"Skills directory not found: {self.skills_dir}")
            return
        
        import yaml
        
        for skill_file in self.skills_dir.glob("*.yaml"):
            try:
                with open(skill_file, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                # Convert to SkillConfig
                skill = SkillConfig(**data)
                self._skills_cache[skill.id] = skill
                logger.debug(f"Loaded skill: {skill.id}")
                
            except Exception as e:
                logger.error(f"Error loading skill from {skill_file}: {e}")
    
    def get_skill(self, skill_id: str) -> Optional[SkillConfig]:
        """Get a skill by ID."""
        return self._skills_cache.get(skill_id)
    
    def list_skills(self) -> List[SkillConfig]:
        """List all available skills."""
        return list(self._skills_cache.values())
    
    def _substitute_parameters(
        self, 
        text: str, 
        parameters: Dict[str, Any]
    ) -> str:
        """Substitute {{parameter}} placeholders in text."""
        result = text
        for key, value in parameters.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result
    
    def apply_skill_to_system_prompt(
        self,
        skill: SkillConfig,
        base_prompt: str,
        parameters: Dict[str, Any] = None
    ) -> str:
        """
        Apply a skill as a system prompt extension.
        
        Args:
            skill: Skill configuration
            base_prompt: Base system prompt
            parameters: Parameter values for substitution
            
        Returns:
            Extended system prompt
        """
        parameters = parameters or {}
        
        # Substitute parameters in skill system prompt
        skill_prompt = self._substitute_parameters(skill.system_prompt, parameters)
        
        # Combine prompts
        if base_prompt:
            extended_prompt = f"{base_prompt}\n\n## {skill.name} Skill\n{skill_prompt}"
        else:
            extended_prompt = f"## {skill.name} Skill\n{skill_prompt}"
        
        logger.debug(f"Applied skill '{skill.id}' as system prompt extension")
        return extended_prompt
    
    def apply_skill_as_few_shot_examples(
        self,
        skill: SkillConfig,
        messages: List[Dict[str, str]],
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        Apply a skill by adding few-shot examples to messages.
        
        Args:
            skill: Skill configuration
            messages: Current message list
            parameters: Parameter values for substitution
            
        Returns:
            Updated message list with examples
        """
        parameters = parameters or {}
        
        if not skill.examples:
            logger.debug(f"Skill '{skill.id}' has no examples to add")
            return messages
        
        # Find insertion point (after system message, before user messages)
        insert_idx = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                insert_idx = i + 1
            else:
                break
        
        # Add examples as user/assistant pairs
        example_messages = []
        for example in skill.examples:
            # Substitute parameters in examples
            user_content = self._substitute_parameters(
                example.get("input", ""), 
                parameters
            )
            assistant_content = self._substitute_parameters(
                example.get("output", ""), 
                parameters
            )
            
            if user_content and assistant_content:
                example_messages.append({"role": "user", "content": user_content})
                example_messages.append({"role": "assistant", "content": assistant_content})
        
        # Insert examples
        result = messages[:insert_idx] + example_messages + messages[insert_idx:]
        
        logger.debug(f"Applied skill '{skill.id}' as {len(example_messages)} few-shot examples")
        return result
    
    def apply_skill_as_orchestration(
        self,
        skill: SkillConfig,
        messages: List[Dict[str, str]],
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        Apply a skill by adding orchestration steps as context.
        
        Args:
            skill: Skill configuration
            messages: Current message list
            parameters: Parameter values for substitution
            
        Returns:
            Updated message list with orchestration context
        """
        parameters = parameters or {}
        
        if not skill.orchestration_steps:
            logger.debug(f"Skill '{skill.id}' has no orchestration steps")
            return messages
        
        # Build orchestration instructions
        steps_text = f"## {skill.name} - Orchestration Steps\n\n"
        steps_text += "Follow these steps to complete the task:\n\n"
        
        # Sort steps by step_number
        sorted_steps = sorted(skill.orchestration_steps, key=lambda s: s.step_number)
        
        for step in sorted_steps:
            instruction = self._substitute_parameters(step.instruction, parameters)
            steps_text += f"{step.step_number}. {instruction}"
            
            if step.expected_output:
                expected = self._substitute_parameters(step.expected_output, parameters)
                steps_text += f"\n   Expected output: {expected}"
            
            if step.depends_on:
                steps_text += f"\n   Depends on steps: {', '.join(map(str, step.depends_on))}"
            
            if step.optional:
                steps_text += "\n   (Optional step)"
            
            steps_text += "\n\n"
        
        # Add as system message or context
        orchestration_msg = {
            "role": "system",
            "content": steps_text
        }
        
        # Insert after existing system messages
        insert_idx = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                insert_idx = i + 1
        
        result = messages[:insert_idx] + [orchestration_msg] + messages[insert_idx:]
        
        logger.debug(f"Applied skill '{skill.id}' as orchestration with {len(sorted_steps)} steps")
        return result
    
    def apply_skill_as_context(
        self,
        skill: SkillConfig,
        messages: List[Dict[str, str]],
        parameters: Dict[str, Any] = None
    ) -> List[Dict[str, str]]:
        """
        Apply a skill by injecting context before user message.
        
        Args:
            skill: Skill configuration
            messages: Current message list
            parameters: Parameter values for substitution
            
        Returns:
            Updated message list with context injection
        """
        parameters = parameters or {}
        
        if not skill.context_template:
            logger.debug(f"Skill '{skill.id}' has no context template")
            return messages
        
        # Substitute parameters in context template
        context = self._substitute_parameters(skill.context_template, parameters)
        
        # Add as system message before user messages
        context_msg = {
            "role": "system",
            "content": f"## {skill.name} Context\n{context}"
        }
        
        # Insert after existing system messages
        insert_idx = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                insert_idx = i + 1
        
        result = messages[:insert_idx] + [context_msg] + messages[insert_idx:]
        
        logger.debug(f"Applied skill '{skill.id}' as context injection")
        return result
    
    def apply_skill(
        self,
        skill: SkillConfig,
        system_prompt: str,
        messages: List[Dict[str, str]],
        application_modes: List[SkillApplicationMode],
        parameters: Dict[str, Any] = None
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        Apply a skill using specified application modes.
        
        Args:
            skill: Skill configuration
            system_prompt: Current system prompt
            messages: Current message list
            application_modes: How to apply the skill
            parameters: Parameter values for substitution
            
        Returns:
            Tuple of (updated_system_prompt, updated_messages)
        """
        parameters = parameters or {}
        updated_prompt = system_prompt
        updated_messages = messages.copy()
        
        # Handle ALL mode
        if SkillApplicationMode.ALL in application_modes:
            application_modes = [
                SkillApplicationMode.SYSTEM_PROMPT_EXTENSION,
                SkillApplicationMode.FEW_SHOT_EXAMPLES,
                SkillApplicationMode.ORCHESTRATION_STEP,
                SkillApplicationMode.CONTEXT_INJECTION
            ]
        
        # Apply each mode
        for mode in application_modes:
            if mode == SkillApplicationMode.SYSTEM_PROMPT_EXTENSION:
                updated_prompt = self.apply_skill_to_system_prompt(
                    skill, updated_prompt, parameters
                )
            elif mode == SkillApplicationMode.FEW_SHOT_EXAMPLES:
                updated_messages = self.apply_skill_as_few_shot_examples(
                    skill, updated_messages, parameters
                )
            elif mode == SkillApplicationMode.ORCHESTRATION_STEP:
                updated_messages = self.apply_skill_as_orchestration(
                    skill, updated_messages, parameters
                )
            elif mode == SkillApplicationMode.CONTEXT_INJECTION:
                updated_messages = self.apply_skill_as_context(
                    skill, updated_messages, parameters
                )
        
        logger.info(f"Applied skill '{skill.id}' with modes: {[m.value for m in application_modes]}")
        return updated_prompt, updated_messages
    
    def load_and_apply_skills(
        self,
        skill_instances: List[Union[str, SkillInstance]],
        system_prompt: str,
        messages: List[Dict[str, str]],
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ) -> tuple[str, List[Dict[str, str]]]:
        """
        Load and apply multiple skills to an agent.
        
        Args:
            skill_instances: List of skill IDs or SkillInstance objects
            system_prompt: Base system prompt
            messages: Base message list
            trace_id: Optional trace ID for telemetry
            parent_span_id: Optional parent span ID for telemetry
            
        Returns:
            Tuple of (final_system_prompt, final_messages)
        """
        if not skill_instances:
            return system_prompt, messages
        
        # Start telemetry span for skill application
        skill_span = None
        if trace_id:
            skill_span = self.telemetry_service.log_action(
                trace_id=trace_id,
                parent_span_id=parent_span_id,
                action_type=ActionType.CUSTOM,
                name="apply_skills",
                attributes={"skill_count": len(skill_instances)},
                kind=SpanKind.INTERNAL
            )
        
        # Normalize to SkillInstance objects
        normalized_instances: List[SkillInstance] = []
        for item in skill_instances:
            if isinstance(item, str):
                # Simple skill ID - use defaults
                normalized_instances.append(SkillInstance(skill_id=item))
            else:
                # Already a SkillInstance
                normalized_instances.append(item)
        
        # Sort by priority (higher priority first)
        sorted_instances = sorted(
            normalized_instances, 
            key=lambda x: x.priority, 
            reverse=True
        )
        
        # Apply each skill
        current_prompt = system_prompt
        current_messages = messages
        
        for instance in sorted_instances:
            if not instance.enabled:
                logger.debug(f"Skipping disabled skill instance: {instance.skill_id}")
                continue
            
            # Load skill config
            skill = self.get_skill(instance.skill_id)
            if not skill:
                logger.warning(f"Skill not found: {instance.skill_id}")
                continue
            
            if not skill.enabled:
                logger.debug(f"Skipping disabled skill: {instance.skill_id}")
                continue
            
            # Determine application modes
            modes = instance.application_modes or skill.default_application_modes
            
            # Apply skill
            current_prompt, current_messages = self.apply_skill(
                skill=skill,
                system_prompt=current_prompt,
                messages=current_messages,
                application_modes=modes,
                parameters=instance.parameters
            )
        
        logger.info(f"Applied {len(sorted_instances)} skills to agent")
        
        # Complete telemetry span
        if skill_span:
            self.telemetry_service.complete_action(
                span_id=skill_span.span_id,
                status=SpanStatus.OK,
                output_data={"skills_applied": len(sorted_instances)}
            )
        
        return current_prompt, current_messages


# Singleton instance
_skill_service: Optional[SkillService] = None


def get_skill_service() -> SkillService:
    """Get the skill service singleton."""
    global _skill_service
    if _skill_service is None:
        _skill_service = SkillService()
    return _skill_service

"""
Skills model for reusable agent capabilities.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.base import ADKComponentConfig, ComponentType


class SkillApplicationMode(str, Enum):
    """How a skill should be applied to an agent."""
    SYSTEM_PROMPT_EXTENSION = "system_prompt_extension"  # Extend system prompt
    FEW_SHOT_EXAMPLES = "few_shot_examples"  # Add few-shot examples to messages
    ORCHESTRATION_STEP = "orchestration_step"  # Add as orchestration/planning step
    CONTEXT_INJECTION = "context_injection"  # Inject as context before user message
    ALL = "all"  # Apply all modes


class SkillCategory(str, Enum):
    """Categories of skills."""
    REASONING = "reasoning"
    CODING = "coding"
    WRITING = "writing"
    ANALYSIS = "analysis"
    RESEARCH = "research"
    COMMUNICATION = "communication"
    DATA_PROCESSING = "data_processing"
    CREATIVE = "creative"
    DOMAIN_SPECIFIC = "domain_specific"
    CUSTOM = "custom"


class SkillParameter(BaseModel):
    """Configurable parameter for a skill."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(default="string", description="Parameter type: string, integer, float, boolean, array, object")
    description: str = Field(default="", description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    enum: Optional[List[Any]] = Field(default=None, description="Allowed values")
    min_value: Optional[float] = Field(default=None, description="Minimum value for numeric types")
    max_value: Optional[float] = Field(default=None, description="Maximum value for numeric types")


class OrchestrationStep(BaseModel):
    """Defines an orchestration step for a skill."""
    step_number: int = Field(..., description="Order in the orchestration sequence")
    instruction: str = Field(..., description="Instruction for this step")
    expected_output: Optional[str] = Field(default=None, description="Description of expected output")
    depends_on: List[int] = Field(default_factory=list, description="Step numbers this depends on")
    optional: bool = Field(default=False, description="Whether this step is optional")


class SkillConfig(ADKComponentConfig):
    """
    Configuration for a reusable skill.
    
    Inherits standard fields from ADKComponentConfig:
    - id, name, description, version
    - component_type, status, enabled
    - tags, category, metadata
    - jwt_required, allowed_groups, allowed_roles
    - dependencies, created_at, updated_at, created_by
    """
    # Override component type
    component_type: ComponentType = Field(default=ComponentType.SKILL)
    
    # Skill category
    skill_category: SkillCategory = Field(default=SkillCategory.CUSTOM, description="Skill category")
    
    # Application modes - how this skill should be applied
    default_application_modes: List[SkillApplicationMode] = Field(
        default_factory=lambda: [SkillApplicationMode.SYSTEM_PROMPT_EXTENSION],
        description="Default modes for applying this skill"
    )
    
    # Skill definition
    system_prompt: str = Field(..., description="System prompt that defines this skill")
    examples: List[Dict[str, str]] = Field(default_factory=list, description="Few-shot examples for demonstration")
    
    # Orchestration steps (for workflow/planning skills)
    orchestration_steps: List[OrchestrationStep] = Field(
        default_factory=list,
        description="Step-by-step orchestration instructions"
    )
    
    # Context template (for context injection mode)
    context_template: Optional[str] = Field(
        default=None,
        description="Template for injecting skill context before user message"
    )
    
    # Configurable parameters
    parameters: List[SkillParameter] = Field(default_factory=list, description="Configurable parameters")
    
    # Required capabilities
    required_tools: List[str] = Field(default_factory=list, description="Tool IDs required for this skill")
    required_capabilities: List[str] = Field(default_factory=list, description="Agent capabilities required")
    
    # Skill-specific metadata
    author: Optional[str] = Field(default=None, description="Skill author")
    use_cases: List[str] = Field(default_factory=list, description="Example use cases")
    
    # Rating and usage
    rating: float = Field(default=0.0, ge=0.0, le=5.0, description="Average rating")
    usage_count: int = Field(default=0, description="Number of times used")


class SkillInstance(BaseModel):
    """An instance of a skill with configured parameters and application modes."""
    skill_id: str = Field(..., description="Reference to skill template")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Configured parameter values")
    application_modes: Optional[List[SkillApplicationMode]] = Field(
        default=None,
        description="Override default application modes for this instance"
    )
    priority: int = Field(default=0, description="Priority order for applying skills (higher = earlier)")
    enabled: bool = Field(default=True, description="Whether this skill instance is enabled")


class SkillResponse(BaseModel):
    """Response for a single skill."""
    success: bool = Field(default=True)
    skill: Optional[SkillConfig] = Field(default=None)
    error: Optional[str] = Field(default=None)


class SkillListResponse(BaseModel):
    """Response for listing skills."""
    success: bool = Field(default=True)
    skills: List[SkillConfig] = Field(default_factory=list)
    total: int = Field(default=0)

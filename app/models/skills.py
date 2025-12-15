"""
Skills model for reusable agent capabilities.
"""
from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


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


class SkillConfig(BaseModel):
    """Configuration for a reusable skill."""
    id: str = Field(..., description="Unique skill identifier")
    name: str = Field(..., description="Human-readable skill name")
    description: str = Field(..., description="Detailed skill description")
    category: SkillCategory = Field(default=SkillCategory.CUSTOM)
    version: str = Field(default="1.0.0")
    
    # Skill definition
    system_prompt: str = Field(..., description="System prompt that defines this skill")
    examples: List[Dict[str, str]] = Field(default_factory=list, description="Few-shot examples")
    
    # Configurable parameters
    parameters: List[SkillParameter] = Field(default_factory=list, description="Configurable parameters")
    
    # Required capabilities
    required_tools: List[str] = Field(default_factory=list, description="Tool IDs required for this skill")
    required_capabilities: List[str] = Field(default_factory=list, description="Agent capabilities required")
    
    # Metadata
    author: Optional[str] = Field(default=None)
    tags: List[str] = Field(default_factory=list)
    use_cases: List[str] = Field(default_factory=list, description="Example use cases")
    
    # Versioning
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)
    
    # Rating and usage
    rating: float = Field(default=0.0, ge=0.0, le=5.0)
    usage_count: int = Field(default=0)
    
    class Config:
        extra = "allow"


class SkillInstance(BaseModel):
    """An instance of a skill with configured parameters."""
    skill_id: str = Field(..., description="Reference to skill template")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Configured parameter values")
    enabled: bool = Field(default=True)


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

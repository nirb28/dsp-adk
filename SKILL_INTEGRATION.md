# Skill Integration in ADK

## Overview

The Agent Development Kit (ADK) now supports comprehensive skill integration, allowing skills to be configured and applied to agents in multiple ways:

- **System Prompt Extension**: Enhance the agent's system prompt with skill-specific instructions
- **Few-Shot Examples**: Add demonstration examples to guide the agent's behavior
- **Orchestration Steps**: Provide step-by-step workflow instructions
- **Context Injection**: Add contextual information before user messages

## Key Features

### 1. Skill Application Modes

Skills can be applied in four different modes:

```python
class SkillApplicationMode(str, Enum):
    SYSTEM_PROMPT_EXTENSION = "system_prompt_extension"
    FEW_SHOT_EXAMPLES = "few_shot_examples"
    ORCHESTRATION_STEP = "orchestration_step"
    CONTEXT_INJECTION = "context_injection"
    ALL = "all"  # Apply all modes
```

### 2. Skill Configuration

Skills are defined in YAML files with the following structure:

```yaml
id: skill-id
name: Skill Name
description: Skill description
category: reasoning  # or coding, writing, analysis, etc.
version: "1.0.0"

# Default application modes
default_application_modes:
  - system_prompt_extension
  - few_shot_examples

# System prompt that defines the skill
system_prompt: |
  Instructions for applying this skill...

# Few-shot examples (for demonstration)
examples:
  - input: "Example user input"
    output: "Example assistant output"

# Orchestration steps (for workflow skills)
orchestration_steps:
  - step_number: 1
    instruction: "Step instruction"
    expected_output: "What this step should produce"
    depends_on: []  # Dependencies on other steps
    optional: false

# Context template (for context injection)
context_template: |
  Context information with {{parameter}} placeholders

# Configurable parameters
parameters:
  - name: parameter_name
    type: string
    description: Parameter description
    required: false
    default: default_value
```

### 3. Agent Configuration with Skills

Agents can be configured with skills in two ways:

#### Simple Configuration (Skill ID only)
```yaml
skills:
  - code-generation
  - information-synthesis
```

#### Advanced Configuration (SkillInstance objects)
```yaml
skills:
  - skill_id: research-methodology
    application_modes:
      - context_injection
      - system_prompt_extension
    parameters:
      research_depth: standard
      source_types: "academic, news"
      require_citations: true
    priority: 10  # Higher priority = applied first
    enabled: true
    
  - skill_id: information-synthesis
    application_modes:
      - system_prompt_extension
    parameters:
      output_structure: hierarchical
      detail_level: moderate
    priority: 5
    enabled: true
```

## Skill Application Modes Explained

### System Prompt Extension

Extends the agent's system prompt with skill-specific instructions.

**Use Case**: Add specialized knowledge or behavioral guidelines to the agent.

**Example**:
```python
# Base prompt
"You are a helpful assistant."

# After applying code-generation skill
"You are a helpful assistant.

## Code Generation Skill
When generating code:
1. Write clean, readable code following best practices
2. Include appropriate error handling
..."
```

### Few-Shot Examples

Adds demonstration examples to the message history to guide the agent's behavior.

**Use Case**: Show the agent how to format responses or handle specific types of requests.

**Example**:
```python
# Messages before
[
  {"role": "system", "content": "You are a coding assistant."},
  {"role": "user", "content": "Write a function to sort a list"}
]

# Messages after (with code-generation skill examples)
[
  {"role": "system", "content": "You are a coding assistant."},
  {"role": "user", "content": "Write a function to validate email addresses"},
  {"role": "assistant", "content": "```python\ndef validate_email(email: str) -> bool:..."},
  {"role": "user", "content": "Create a function to calculate fibonacci numbers"},
  {"role": "assistant", "content": "```python\ndef fibonacci(n: int) -> int:..."},
  {"role": "user", "content": "Write a function to sort a list"}
]
```

### Orchestration Steps

Provides step-by-step workflow instructions for complex tasks.

**Use Case**: Guide the agent through a structured process with dependencies.

**Example**:
```python
# Adds orchestration message
{
  "role": "system",
  "content": """
## Task Decomposition - Orchestration Steps

Follow these steps to complete the task:

1. Understand the overall goal and define clear success criteria
   Expected output: A clear statement of the goal and measurable success criteria

2. Identify the main components or phases of the task
   Expected output: A list of 3-7 major components or phases
   Depends on steps: 1

3. Break each component into atomic, actionable subtasks
   Expected output: Detailed subtasks for each component with clear action verbs
   Depends on steps: 2
...
"""
}
```

### Context Injection

Injects contextual information before user messages using parameter substitution.

**Use Case**: Provide dynamic context based on skill parameters.

**Example**:
```python
# With research-methodology skill
{
  "role": "system",
  "content": """
## Research Methodology Context
Research Context:
- Research Depth: comprehensive
- Source Types: academic, peer-reviewed
- Citation Required: true

Guidelines:
- Prioritize peer-reviewed and authoritative sources
- Note any conflicting information found
- Indicate confidence levels for findings
"""
}
```

## Skill Priority and Ordering

Skills are applied in priority order (higher priority first):

```yaml
skills:
  - skill_id: skill-a
    priority: 10  # Applied first
  - skill_id: skill-b
    priority: 5   # Applied second
  - skill_id: skill-c
    priority: 0   # Applied last (default)
```

This allows you to control the order in which skills modify the agent's behavior.

## Parameter Substitution

Skills support parameter substitution using `{{parameter}}` syntax:

```yaml
context_template: |
  Research Depth: {{research_depth}}
  Source Types: {{source_types}}

parameters:
  - name: research_depth
    type: string
    default: standard
```

When applied with parameters:
```python
SkillInstance(
    skill_id="research-methodology",
    parameters={
        "research_depth": "comprehensive",
        "source_types": "academic, peer-reviewed"
    }
)
```

Results in:
```
Research Depth: comprehensive
Source Types: academic, peer-reviewed
```

## Available Skills

### 1. Code Generation
- **Category**: Coding
- **Default Modes**: System prompt extension, Few-shot examples
- **Use Cases**: Function implementation, API development, script creation

### 2. Information Synthesis
- **Category**: Reasoning
- **Default Modes**: System prompt extension
- **Use Cases**: Literature reviews, market research summaries, multi-source analysis

### 3. Task Decomposition
- **Category**: Reasoning
- **Default Modes**: Orchestration step, System prompt extension
- **Use Cases**: Project planning, sprint planning, complex problem solving

### 4. Research Methodology
- **Category**: Research
- **Default Modes**: Context injection, System prompt extension
- **Use Cases**: Academic research, market analysis, fact-checking

### 5. SQL Generation
- **Category**: Data Processing
- **Default Modes**: System prompt extension, Few-shot examples
- **Use Cases**: Database queries, data analysis, reporting

## Usage Examples

### Example 1: Simple Skill Assignment

```python
from app.models.agents import AgentConfig, LLMConfig

agent = AgentConfig(
    id="coding-agent",
    name="Coding Assistant",
    llm=LLMConfig(
        provider="groq",
        model="llama3-8b-8192",
        system_prompt="You are a coding assistant."
    ),
    skills=["code-generation"]  # Simple skill ID
)
```

### Example 2: Advanced Skill Configuration

```python
from app.models.agents import AgentConfig, LLMConfig
from app.models.skills import SkillInstance, SkillApplicationMode

agent = AgentConfig(
    id="research-agent",
    name="Research Assistant",
    llm=LLMConfig(
        provider="groq",
        model="llama3-70b-8192",
        system_prompt="You are a research assistant."
    ),
    skills=[
        SkillInstance(
            skill_id="research-methodology",
            application_modes=[
                SkillApplicationMode.CONTEXT_INJECTION,
                SkillApplicationMode.SYSTEM_PROMPT_EXTENSION
            ],
            parameters={
                "research_depth": "comprehensive",
                "source_types": "academic, peer-reviewed",
                "require_citations": True
            },
            priority=10,
            enabled=True
        ),
        SkillInstance(
            skill_id="information-synthesis",
            application_modes=[SkillApplicationMode.SYSTEM_PROMPT_EXTENSION],
            parameters={
                "output_structure": "hierarchical",
                "detail_level": "comprehensive"
            },
            priority=5,
            enabled=True
        )
    ]
)
```

### Example 3: Orchestration-Focused Agent

```python
agent = AgentConfig(
    id="planning-agent",
    name="Planning Assistant",
    llm=LLMConfig(
        provider="groq",
        model="llama3-70b-8192",
        system_prompt="You are a planning assistant."
    ),
    skills=[
        SkillInstance(
            skill_id="task-decomposition",
            application_modes=[SkillApplicationMode.ORCHESTRATION_STEP],
            parameters={
                "max_depth": 4,
                "output_format": "tree",
                "include_estimates": True
            },
            priority=10,
            enabled=True
        )
    ]
)
```

## Creating Custom Skills

### Step 1: Create Skill YAML File

Create a new file in `data/skills/`:

```yaml
id: my-custom-skill
name: My Custom Skill
description: Description of what this skill does
category: custom
version: "1.0.0"

default_application_modes:
  - system_prompt_extension

system_prompt: |
  Your skill instructions here...

parameters:
  - name: param1
    type: string
    description: Parameter description
    default: default_value

examples:
  - input: "Example input"
    output: "Example output"

tags:
  - custom
  - your-tags

metadata:
  author: your-name
  rating: 0.0
  usage_count: 0
```

### Step 2: Use in Agent Configuration

```yaml
skills:
  - skill_id: my-custom-skill
    parameters:
      param1: custom_value
    enabled: true
```

## Testing

Run the comprehensive test suite:

```bash
python test_skill_integration.py
```

This tests:
1. Skill loading
2. System prompt extension
3. Few-shot examples
4. Orchestration steps
5. Context injection
6. Multiple skills with priorities
7. Full agent execution with skills

## Best Practices

1. **Choose Appropriate Modes**: Select application modes that match your skill's purpose
   - Use **system_prompt_extension** for behavioral guidelines
   - Use **few_shot_examples** for response formatting
   - Use **orchestration_step** for structured workflows
   - Use **context_injection** for dynamic contextual information

2. **Set Priorities Carefully**: Higher priority skills are applied first and can influence later skills

3. **Use Parameters**: Make skills reusable by parameterizing configurable aspects

4. **Provide Examples**: Include few-shot examples to demonstrate expected behavior

5. **Document Dependencies**: Clearly specify required tools and capabilities

6. **Test Combinations**: Test how skills interact when applied together

## Architecture

### Skill Service (`app/services/skill_service.py`)

Handles:
- Loading skill configurations from YAML files
- Applying skills in different modes
- Parameter substitution
- Priority-based skill ordering

### Agent Executor Integration (`app/services/agent_executor.py`)

- Automatically applies skills during message building
- Integrates with existing tool and LLM systems
- Maintains backward compatibility

### Models

- `SkillConfig`: Defines a reusable skill
- `SkillInstance`: Configures a skill for a specific agent
- `SkillApplicationMode`: Enum of application modes
- `OrchestrationStep`: Defines workflow steps

## Troubleshooting

### Skills Not Applied

- Check that skill files exist in `data/skills/`
- Verify skill IDs match exactly
- Ensure skills are enabled (`enabled: true`)
- Check logs for skill loading errors

### Parameters Not Substituted

- Verify parameter names match exactly (case-sensitive)
- Use `{{parameter}}` syntax in templates
- Check that parameters are provided in SkillInstance

### Orchestration Steps Not Showing

- Ensure skill has `orchestration_steps` defined
- Use `orchestration_step` application mode
- Check that steps have valid structure

## Future Enhancements

- Dynamic skill discovery and registration
- Skill versioning and compatibility checking
- Skill composition and chaining
- Performance metrics per skill
- Skill marketplace integration

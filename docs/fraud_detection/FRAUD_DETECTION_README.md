# Check Fraud Detection System

## Overview

This comprehensive fraud detection system uses multi-agent voting with LangGraph to analyze checks for potential fraud. The system employs three specialized AI agents that work in parallel to examine different aspects of check authenticity:

1. **Signature Agent** (35% weight) - Analyzes signature authenticity and detects forgeries
2. **Watermark Agent** (25% weight) - Verifies watermarks and security features
3. **Tampering Agent** (40% weight) - Detects image alterations and tampering

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Check Image Input                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
        ┌───────────────────────────────────────┐
        │      LangGraph Workflow (Parallel)     │
        └───────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Signature   │   │  Watermark   │   │  Tampering   │
│    Agent     │   │    Agent     │   │    Agent     │
│  (35% wt)    │   │  (25% wt)    │   │  (40% wt)    │
└──────────────┘   └──────────────┘   └──────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                ┌───────────────────────┐
                │   Weighted Voting     │
                │   & Consensus Check   │
                └───────────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │   Final Decision      │
                │ APPROVE/REVIEW/REJECT │
                └───────────────────────┘
```

## Components

### 1. Image Fraud Detector Tool

**File:** `tools/image_fraud_detector.py`

Core tool providing fraud detection capabilities:

- **Signature Analysis**: Compares signatures using stroke patterns, pen pressure, letter formation
- **Watermark Detection**: Identifies security features, microprinting, holograms
- **Tampering Detection**: Detects erasures, alterations, inconsistent fonts, digital manipulation
- **Comprehensive Analysis**: Combines all methods for complete fraud assessment

**Key Features:**
- Base64 image encoding for API transmission
- OpenAI-compatible vision API integration
- Detailed debug logging at every step
- JSON response parsing with error handling
- Configurable analysis prompts

### 2. Specialized Agents

#### Signature Agent
**File:** `data/agents/fraud-signature-agent.yaml`

Expertise:
- Handwriting analysis
- Signature comparison
- Forgery detection
- Stroke pattern analysis

Decision Weight: 35%

#### Watermark Agent
**File:** `data/agents/fraud-watermark-agent.yaml`

Expertise:
- Watermark detection
- Security feature verification
- Microprinting identification
- Hologram validation

Decision Weight: 25%

#### Tampering Agent
**File:** `data/agents/fraud-tampering-agent.yaml`

Expertise:
- Alteration detection
- Erasure identification
- Font consistency analysis
- Digital manipulation detection

Decision Weight: 40%

### 3. LangGraph Workflow

**File:** `data/graphs/fraud-detection-voting.yaml`

Orchestrates parallel agent execution and voting:

- **Parallel Execution**: All agents run simultaneously for efficiency
- **State Management**: Maintains analysis state across workflow
- **Voting Node**: Aggregates results using weighted scoring
- **Consensus Detection**: Identifies when agents agree/disagree

### 4. Multi-Agent Voting System

**File:** `examples/fraud_detection_example.py`

Implements the complete voting and decision-making logic:

```python
# Weighted scoring formula
weighted_score = Σ(agent_score × agent_weight)

# Decision thresholds
REJECT:  fraud_score >= 70
REVIEW:  40 <= fraud_score < 70
APPROVE: fraud_score < 40
```

**Confidence Levels:**
- **HIGH**: All agents agree (consensus)
- **MEDIUM**: 60%+ weighted agreement
- **LOW**: Split decision

## Usage

### Basic Example

```python
from examples.fraud_detection_example import FraudDetectionVotingSystem

# Initialize system
voting_system = FraudDetectionVotingSystem(
    llm_endpoint="https://api.openai.com/v1/chat/completions",
    llm_api_key="your-api-key",
    model="gpt-4-vision-preview"
)

# Analyze check
result = voting_system.analyze_check(
    check_image="data/checks/check_001.jpg",
    comparison_signatures=[
        "data/signatures/sig_001.jpg",
        "data/signatures/sig_002.jpg"
    ],
    expected_watermark="Bank of America watermark",
    focus_areas=["amount", "payee", "date"]
)

# Review decision
print(f"Decision: {result['final_decision']}")
print(f"Confidence: {result['decision_confidence']}")
print(f"Fraud Score: {result['weighted_fraud_score']:.2f}/100")
```

### Running the Example

```bash
# Set environment variables
export OPENAI_API_ENDPOINT="https://api.openai.com/v1/chat/completions"
export OPENAI_API_KEY="your-api-key-here"
export VISION_MODEL="gpt-4-vision-preview"

# Run the example
cd examples
python fraud_detection_example.py
```

## Debug Logging

The system provides comprehensive debug logging at multiple levels:

### Log Levels

1. **[INIT]** - System initialization
2. **[SIGNATURE_AGENT]** - Signature analysis steps
3. **[WATERMARK_AGENT]** - Watermark verification steps
4. **[TAMPERING_AGENT]** - Tampering detection steps
5. **[VOTING]** - Vote aggregation and decision-making
6. **[SCORE_CALC]** - Fraud score calculations
7. **[RISK_ASSESSMENT]** - Risk level determination
8. **[RECOMMENDATIONS]** - Action recommendations

### Example Log Output

```
2024-01-13 14:30:00 - INFO - ================================================================================
2024-01-13 14:30:00 - INFO - STARTING MULTI-AGENT FRAUD DETECTION ANALYSIS
2024-01-13 14:30:00 - INFO - ================================================================================
2024-01-13 14:30:01 - INFO - [WORKFLOW] Executing agents in parallel...
2024-01-13 14:30:02 - INFO - ┌──────────────────────────────────────────────────────────────────────────────┐
2024-01-13 14:30:02 - INFO - │ SIGNATURE AGENT ANALYSIS                                                     │
2024-01-13 14:30:02 - INFO - └──────────────────────────────────────────────────────────────────────────────┘
2024-01-13 14:30:05 - INFO - [SIGNATURE_AGENT] ✓ Analysis complete
2024-01-13 14:30:05 - INFO - [SIGNATURE_AGENT] Fraud Score: 25/100
2024-01-13 14:30:05 - INFO - [SIGNATURE_AGENT] Recommendation: APPROVE
...
2024-01-13 14:30:15 - INFO - [VOTING] Weighted Fraud Score: 32.50/100
2024-01-13 14:30:15 - INFO - ================================================================================
2024-01-13 14:30:15 - INFO - FINAL DECISION
2024-01-13 14:30:15 - INFO - ================================================================================
2024-01-13 14:30:15 - INFO - Decision: APPROVE
2024-01-13 14:30:15 - INFO - Confidence: HIGH
2024-01-13 14:30:15 - INFO - Fraud Score: 32.50/100
2024-01-13 14:30:15 - INFO - Consensus: Yes
```

## Decision Logic

### Fraud Score Calculation

Each agent provides a fraud score (0-100):
- **0**: No fraud indicators
- **50**: Moderate concern
- **100**: Definite fraud

The final score is calculated using weighted averaging:

```
Final Score = (Signature × 0.35) + (Watermark × 0.25) + (Tampering × 0.40)
```

### Recommendation Mapping

| Fraud Score | Decision | Action |
|-------------|----------|--------|
| 0-39 | APPROVE | Process with standard verification |
| 40-69 | REVIEW | Manual review required |
| 70-100 | REJECT | Do not process - high fraud risk |

### Consensus Analysis

The system checks if agents agree:
- **Full Consensus**: All agents recommend the same action → HIGH confidence
- **Majority (60%+)**: Weighted majority agrees → MEDIUM confidence
- **Split Decision**: No clear majority → LOW confidence

## Fraud Indicators

### Signature Fraud Indicators
- Inconsistent stroke patterns
- Uniform pen pressure (tracing)
- Shaky or hesitant lines
- Different letter formation
- Size/proportion mismatches

### Watermark Fraud Indicators
- Missing watermark
- Incorrect watermark design
- Tampered or removed watermark
- Missing security features
- Inconsistent paper quality

### Tampering Fraud Indicators
- Erasure marks
- Correction fluid usage
- Inconsistent fonts
- Different ink colors
- Misaligned text
- Digital manipulation artifacts
- Overwriting or alterations

## Output Format

The system returns a comprehensive JSON result:

```json
{
  "final_decision": "APPROVE|REVIEW|REJECT",
  "decision_confidence": "LOW|MEDIUM|HIGH",
  "weighted_fraud_score": 32.50,
  "consensus": true,
  "decision_reasoning": "Detailed explanation...",
  "vote_distribution": {
    "APPROVE": 1.0,
    "REVIEW": 0.0,
    "REJECT": 0.0
  },
  "agent_votes": [
    {
      "agent": "signature",
      "fraud_score": 25,
      "recommendation": "APPROVE",
      "confidence": "high",
      "details": "...",
      "indicators": []
    },
    {
      "agent": "watermark",
      "fraud_score": 20,
      "recommendation": "APPROVE",
      "confidence": "high",
      "watermark_present": true,
      "watermark_valid": true
    },
    {
      "agent": "tampering",
      "fraud_score": 45,
      "recommendation": "REVIEW",
      "confidence": "medium",
      "tampering_detected": false,
      "tampered_areas": []
    }
  ],
  "timestamp": "2024-01-13T14:30:15.123456"
}
```

## Configuration

### Environment Variables

```bash
# Required
OPENAI_API_ENDPOINT=https://api.openai.com/v1/chat/completions
OPENAI_API_KEY=your-api-key-here

# Optional
VISION_MODEL=gpt-4-vision-preview  # Default model
```

### Agent Weights

Modify weights in `FraudDetectionVotingSystem.__init__()`:

```python
self.agent_weights = {
    "signature": 0.35,  # 35% weight
    "watermark": 0.25,  # 25% weight
    "tampering": 0.40   # 40% weight
}
```

### Decision Thresholds

Modify thresholds in agent methods:

```python
if fraud_score >= 70:
    recommendation = "REJECT"
elif fraud_score >= 40:
    recommendation = "REVIEW"
else:
    recommendation = "APPROVE"
```

## Requirements

- Python 3.8+
- OpenAI-compatible vision API access
- Required packages:
  - `requests`
  - `Pillow` (for image handling)
  - `pydantic` (for data validation)

## Best Practices

1. **Image Quality**: Use high-resolution check images (300+ DPI)
2. **Signature Samples**: Provide 3+ valid signature samples for comparison
3. **Watermark Description**: Be specific about expected security features
4. **Focus Areas**: Always include critical fields (amount, payee, signature)
5. **Manual Review**: Always manually review REVIEW decisions
6. **Logging**: Monitor logs for patterns and system performance
7. **Threshold Tuning**: Adjust thresholds based on your risk tolerance

## Troubleshooting

### Common Issues

**Issue**: Low confidence scores
- **Solution**: Provide more signature samples, improve image quality

**Issue**: API timeout errors
- **Solution**: Reduce image size, increase timeout in `_call_vision_api()`

**Issue**: Inconsistent results
- **Solution**: Use higher temperature=0.1 for more deterministic results

**Issue**: Missing fraud indicators
- **Solution**: Enhance agent prompts with specific patterns to look for

## Future Enhancements

- [ ] Support for multiple check types (personal, business, cashier's)
- [ ] Historical fraud pattern learning
- [ ] Integration with bank verification APIs
- [ ] Real-time processing pipeline
- [ ] Mobile app integration
- [ ] Batch processing support
- [ ] Custom agent training for specific fraud types
- [ ] Integration with document verification services

## License

See main ADK LICENSE file.

## Support

For issues or questions, refer to the main ADK documentation or create an issue in the repository.

# Fraud Detection Module

## Overview

This directory contains all components for the check fraud detection system with multi-agent voting.

## Directory Structure

```
fraud_detection/
├── agents/                          # Specialized fraud detection agents
│   ├── fraud-signature-agent.yaml   # Signature analysis agent (35% weight)
│   ├── fraud-watermark-agent.yaml   # Watermark verification agent (25% weight)
│   └── fraud-tampering-agent.yaml   # Tampering detection agent (40% weight)
│
├── graphs/                          # LangGraph workflows
│   └── fraud-detection-voting.yaml  # Multi-agent voting workflow
│
├── tools/                           # Tool configurations
│   └── image-fraud-detector.yaml    # Image fraud detector tool config
│
├── sample_checks/                   # Sample check images (gitignored)
│   └── .gitkeep
│
├── sample_signatures/               # Sample signature images (gitignored)
│   └── .gitkeep
│
├── test_results/                    # Analysis results (gitignored)
│   └── .gitkeep
│
├── README.md                        # This file
└── SAMPLE_IMAGES_GUIDE.md          # Guide for obtaining test images
```

## Quick Start

### 1. Generate Test Data

```bash
# Run the setup script to create sample images
python setup_test_data.py
```

This creates:
- 3 sample check images (including 1 with intentional fraud indicators)
- 5 signature samples with natural variations

### 2. Run Tests

```bash
# Run the test suite (no images required)
python test_fraud_detection.py
```

### 3. Run Full Example

```bash
# Set environment variables
$env:OPENAI_API_KEY="your-api-key"
$env:OPENAI_API_ENDPOINT="https://api.openai.com/v1/chat/completions"

# Run the fraud detection example
python examples/fraud_detection/fraud_detection_example.py
```

## Components

### Agents

Each agent specializes in a specific aspect of fraud detection:

1. **Signature Agent** (`agents/fraud-signature-agent.yaml`)
   - Analyzes signature authenticity
   - Compares against known valid samples
   - Detects forgery indicators
   - Weight: 35%

2. **Watermark Agent** (`agents/fraud-watermark-agent.yaml`)
   - Verifies watermarks and security features
   - Detects missing or tampered watermarks
   - Identifies microprinting and holograms
   - Weight: 25%

3. **Tampering Agent** (`agents/fraud-tampering-agent.yaml`)
   - Detects image alterations
   - Identifies erasures and corrections
   - Spots inconsistent fonts or inks
   - Weight: 40%

### Workflow

The LangGraph workflow (`graphs/fraud-detection-voting.yaml`) orchestrates:
- Parallel execution of all three agents
- State management across the workflow
- Weighted voting and consensus detection
- Final decision generation

### Tool

The image fraud detector tool (`tools/image-fraud-detector.yaml`) provides:
- Signature analysis
- Watermark detection
- Tampering detection
- Comprehensive fraud analysis

## Usage

### Basic Analysis

```python
from examples.fraud_detection.fraud_detection_example import FraudDetectionVotingSystem

# Initialize
system = FraudDetectionVotingSystem(
    llm_endpoint="https://api.openai.com/v1/chat/completions",
    llm_api_key="your-api-key",
    model="gpt-4-vision-preview"
)

# Analyze check
result = system.analyze_check(
    check_image="data/fraud_detection/sample_checks/check_001.jpg",
    comparison_signatures=[
        "data/fraud_detection/sample_signatures/sig_001.jpg",
        "data/fraud_detection/sample_signatures/sig_002.jpg",
        "data/fraud_detection/sample_signatures/sig_003.jpg"
    ],
    expected_watermark="SAMPLE watermark",
    focus_areas=["amount", "payee", "date"]
)

# Review decision
print(f"Decision: {result['final_decision']}")
print(f"Fraud Score: {result['weighted_fraud_score']:.2f}/100")
```

## Decision Logic

### Fraud Score Calculation

```
Final Score = (Signature × 0.35) + (Watermark × 0.25) + (Tampering × 0.40)
```

### Decision Thresholds

| Score | Risk | Decision | Action |
|-------|------|----------|--------|
| 0-39 | LOW | APPROVE | Process with standard verification |
| 40-69 | MEDIUM | REVIEW | Manual review required |
| 70-100 | HIGH | REJECT | Do not process - high fraud risk |

### Confidence Levels

- **HIGH**: All agents agree (consensus)
- **MEDIUM**: 60%+ weighted agreement
- **LOW**: Split decision

## Sample Images

### Creating Test Data

Run the setup script:
```bash
python setup_test_data.py
```

Or see `SAMPLE_IMAGES_GUIDE.md` for:
- Public domain check templates
- AI-generated synthetic checks
- Programmatic image generation
- Signature sample creation

### Image Requirements

**Check Images:**
- Format: JPG, PNG
- Resolution: 300 DPI minimum
- Size: 1800x825 pixels (standard US check)
- Quality: High quality, no blur

**Signature Images:**
- Format: JPG, PNG
- Resolution: 150 DPI minimum
- Size: 600x200 pixels recommended
- Quantity: 3-5 samples for best results

## Security

⚠️ **IMPORTANT**: Never use real checks or signatures!

- All sample data directories are gitignored
- Use only synthetic or public domain images
- Follow PCI-DSS compliance guidelines
- Encrypt sensitive data at rest

## Documentation

- **Main Documentation**: `docs/fraud_detection/FRAUD_DETECTION_README.md`
- **Quick Start**: `docs/fraud_detection/FRAUD_DETECTION_QUICKSTART.md`
- **Implementation Details**: `docs/fraud_detection/IMPLEMENTATION_SUMMARY.md`
- **Sample Images Guide**: `SAMPLE_IMAGES_GUIDE.md`

## File Locations

### Source Code
- Tool implementation: `tools/fraud_detection/image_fraud_detector.py`
- Example script: `examples/fraud_detection/fraud_detection_example.py`
- Test suite: `test_fraud_detection.py` (project root)
- Setup script: `setup_test_data.py` (project root)

### Configuration
- Agent configs: `data/fraud_detection/agents/`
- Graph workflow: `data/fraud_detection/graphs/`
- Tool config: `data/fraud_detection/tools/`

### Documentation
- All docs: `docs/fraud_detection/`

## Troubleshooting

### Issue: Import errors
```python
# Ensure correct import path
from tools.fraud_detection.image_fraud_detector import ImageFraudDetector
```

### Issue: No sample images
```bash
# Generate test data
python setup_test_data.py
```

### Issue: API authentication
```bash
# Check environment variables
echo $env:OPENAI_API_KEY
echo $env:OPENAI_API_ENDPOINT
```

## Next Steps

1. Generate test data: `python setup_test_data.py`
2. Run tests: `python test_fraud_detection.py`
3. Review generated images in `sample_checks/` and `sample_signatures/`
4. Run full example with your API credentials
5. Customize agent weights and thresholds as needed
6. Integrate with your check processing pipeline

## Support

For detailed information, see the documentation in `docs/fraud_detection/`.

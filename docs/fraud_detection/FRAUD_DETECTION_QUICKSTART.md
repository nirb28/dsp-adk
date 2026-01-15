# Fraud Detection Quick Start Guide

## Overview

This guide will help you quickly set up and run the check fraud detection system with multi-agent voting.

## Prerequisites

1. Python 3.8 or higher
2. OpenAI-compatible vision API access (e.g., OpenAI GPT-4 Vision, Azure OpenAI)
3. API key for the vision service

## Installation

### 1. Install Dependencies

```bash
cd dsp-adk
pip install -r requirements.txt
```

Required packages:
- `requests` - For API calls
- `Pillow` - For image handling
- `pydantic` - For data validation
- `pyyaml` - For configuration files

### 2. Set Environment Variables

Create a `.env` file in the project root:

```bash
# Vision API Configuration
OPENAI_API_ENDPOINT=https://api.openai.com/v1/chat/completions
OPENAI_API_KEY=your-api-key-here
VISION_MODEL=gpt-4-vision-preview
```

Or export them directly:

```bash
export OPENAI_API_ENDPOINT="https://api.openai.com/v1/chat/completions"
export OPENAI_API_KEY="your-api-key-here"
export VISION_MODEL="gpt-4-vision-preview"
```

### 3. Prepare Sample Data (Optional)

For testing with real images:

```bash
# Create directories
mkdir -p data/sample_checks
mkdir -p data/sample_signatures

# Add your check images and signature samples
# See data/sample_data_README.md for details
```

## Running the System

### Option 1: Run Tests (No Images Required)

Test the system logic without actual images:

```bash
python test_fraud_detection.py
```

Expected output:
```
================================================================================
FRAUD DETECTION SYSTEM TEST SUITE
================================================================================
...
ALL TESTS PASSED ✓
================================================================================
```

### Option 2: Run Full Example (Images Required)

Run the complete fraud detection example:

```bash
python examples/fraud_detection_example.py
```

This will:
1. Initialize the multi-agent voting system
2. Run three specialized agents in parallel
3. Aggregate results using weighted voting
4. Make a final decision (APPROVE/REVIEW/REJECT)
5. Save results to JSON file

### Option 3: Use as a Library

```python
from examples.fraud_detection_example import FraudDetectionVotingSystem

# Initialize
system = FraudDetectionVotingSystem(
    llm_endpoint="https://api.openai.com/v1/chat/completions",
    llm_api_key="your-api-key",
    model="gpt-4-vision-preview"
)

# Analyze a check
result = system.analyze_check(
    check_image="path/to/check.jpg",
    comparison_signatures=["sig1.jpg", "sig2.jpg", "sig3.jpg"],
    expected_watermark="Bank of America watermark",
    focus_areas=["amount", "payee", "date"]
)

# Review decision
print(f"Decision: {result['final_decision']}")
print(f"Fraud Score: {result['weighted_fraud_score']:.2f}/100")
```

## Understanding the Output

### Console Output

```
================================================================================
STARTING MULTI-AGENT FRAUD DETECTION ANALYSIS
================================================================================
Check Image: data/sample_checks/check_001.jpg
Timestamp: 2024-01-13T14:30:00.123456
================================================================================

[WORKFLOW] Executing agents in parallel...

┌──────────────────────────────────────────────────────────────────────────────┐
│ SIGNATURE AGENT ANALYSIS                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
[SIGNATURE_AGENT] Starting analysis...
[SIGNATURE_AGENT] ✓ Analysis complete
[SIGNATURE_AGENT] Fraud Score: 25/100
[SIGNATURE_AGENT] Recommendation: APPROVE

┌──────────────────────────────────────────────────────────────────────────────┐
│ WATERMARK AGENT ANALYSIS                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
[WATERMARK_AGENT] Starting analysis...
[WATERMARK_AGENT] ✓ Analysis complete
[WATERMARK_AGENT] Fraud Score: 20/100
[WATERMARK_AGENT] Recommendation: APPROVE

┌──────────────────────────────────────────────────────────────────────────────┐
│ TAMPERING AGENT ANALYSIS                                                     │
└──────────────────────────────────────────────────────────────────────────────┘
[TAMPERING_AGENT] Starting analysis...
[TAMPERING_AGENT] ✓ Analysis complete
[TAMPERING_AGENT] Fraud Score: 15/100
[TAMPERING_AGENT] Recommendation: APPROVE

┌──────────────────────────────────────────────────────────────────────────────┐
│ VOTING AND DECISION AGGREGATION                                              │
└──────────────────────────────────────────────────────────────────────────────┘
[VOTING] Weighted Fraud Score: 19.25/100

================================================================================
FINAL DECISION
================================================================================
Decision: APPROVE
Confidence: HIGH
Fraud Score: 19.25/100
Consensus: Yes
================================================================================
```

### JSON Output

Results are saved to `fraud_analysis_YYYYMMDD_HHMMSS.json`:

```json
{
  "final_decision": "APPROVE",
  "decision_confidence": "HIGH",
  "weighted_fraud_score": 19.25,
  "consensus": true,
  "decision_reasoning": "Weighted fraud score: 19.25/100 | Agent consensus: Yes | ...",
  "vote_distribution": {
    "APPROVE": 1.0,
    "REVIEW": 0.0,
    "REJECT": 0.0
  },
  "agent_votes": [...],
  "timestamp": "2024-01-13T14:30:15.123456"
}
```

## Decision Interpretation

### Fraud Score Ranges

| Score | Risk Level | Decision | Action |
|-------|------------|----------|--------|
| 0-39 | LOW | APPROVE | Process with standard verification |
| 40-69 | MEDIUM | REVIEW | Manual review required |
| 70-100 | HIGH | REJECT | Do not process - high fraud risk |

### Confidence Levels

- **HIGH**: All agents agree (consensus reached)
- **MEDIUM**: 60%+ weighted agreement
- **LOW**: Split decision, no clear majority

### Recommendations

Follow these actions based on the decision:

1. **APPROVE**: 
   - Proceed with standard verification
   - Monitor for patterns
   - Log for audit trail

2. **REVIEW**:
   - Manual review by fraud specialist
   - Contact account holder if needed
   - Additional verification steps
   - Document review decision

3. **REJECT**:
   - Do not process the check
   - Flag account for investigation
   - Notify security team
   - Preserve evidence

## Customization

### Adjust Agent Weights

Edit `examples/fraud_detection_example.py`:

```python
self.agent_weights = {
    "signature": 0.35,  # Signature importance
    "watermark": 0.25,  # Watermark importance
    "tampering": 0.40   # Tampering importance
}
```

### Modify Decision Thresholds

```python
# In each agent method
if fraud_score >= 70:
    recommendation = "REJECT"
elif fraud_score >= 40:
    recommendation = "REVIEW"
else:
    recommendation = "APPROVE"
```

### Customize Agent Prompts

Edit agent YAML files in `data/agents/`:
- `fraud-signature-agent.yaml`
- `fraud-watermark-agent.yaml`
- `fraud-tampering-agent.yaml`

## Troubleshooting

### Issue: API Authentication Error

```
Error: 401 Unauthorized
```

**Solution**: Check your API key and endpoint configuration
```bash
echo $OPENAI_API_KEY
echo $OPENAI_API_ENDPOINT
```

### Issue: Image Not Found

```
Error: FileNotFoundError: [Errno 2] No such file or directory
```

**Solution**: Verify image paths are correct
```python
import os
print(os.path.exists("data/sample_checks/check_001.jpg"))
```

### Issue: Low Confidence Scores

```
Decision Confidence: LOW
```

**Solution**: 
- Provide more signature samples (3-5 recommended)
- Use higher resolution images
- Ensure clear, well-lit images

### Issue: API Timeout

```
Error: requests.exceptions.Timeout
```

**Solution**:
- Reduce image file size
- Increase timeout in `_call_vision_api()` method
- Check network connection

### Issue: Inconsistent Results

**Solution**:
- Lower temperature to 0.1 for more deterministic results
- Use same model consistently
- Ensure image quality is consistent

## Performance Tips

1. **Image Optimization**:
   - Compress images to 1-2 MB
   - Use JPEG format for photos
   - Maintain 300 DPI resolution

2. **Batch Processing**:
   - Process multiple checks in parallel
   - Cache signature samples
   - Reuse detector instances

3. **Cost Optimization**:
   - Use lower resolution for initial screening
   - Only run full analysis on flagged items
   - Cache results for duplicate checks

## Security Best Practices

1. **API Key Management**:
   - Never commit API keys to version control
   - Use environment variables or secrets manager
   - Rotate keys regularly

2. **Data Protection**:
   - Encrypt check images at rest
   - Use HTTPS for API calls
   - Delete images after processing

3. **Access Control**:
   - Implement authentication for API access
   - Log all fraud detection requests
   - Restrict access to sensitive results

4. **Compliance**:
   - Follow PCI-DSS guidelines
   - Maintain audit trails
   - Implement data retention policies

## Next Steps

1. **Integration**: Integrate with your check processing system
2. **Monitoring**: Set up logging and alerting
3. **Tuning**: Adjust thresholds based on your fraud patterns
4. **Training**: Train staff on interpreting results
5. **Feedback Loop**: Collect feedback to improve accuracy

## Support

For issues or questions:
1. Check the main documentation: `FRAUD_DETECTION_README.md`
2. Review sample data guide: `data/sample_data_README.md`
3. Run tests: `python test_fraud_detection.py`
4. Check logs: `fraud_detection.log`

## Example Workflow

```bash
# 1. Set up environment
export OPENAI_API_KEY="your-key"
export OPENAI_API_ENDPOINT="https://api.openai.com/v1/chat/completions"

# 2. Run tests to verify setup
python test_fraud_detection.py

# 3. Prepare your data
mkdir -p data/sample_checks data/sample_signatures
# Add your images...

# 4. Run analysis
python examples/fraud_detection_example.py

# 5. Review results
cat fraud_analysis_*.json

# 6. Check logs for details
tail -f fraud_detection.log
```

## Advanced Usage

### Custom Analysis Pipeline

```python
from tools.image_fraud_detector import ImageFraudDetector

# Initialize detector
detector = ImageFraudDetector(
    llm_endpoint=os.getenv("OPENAI_API_ENDPOINT"),
    llm_api_key=os.getenv("OPENAI_API_KEY")
)

# Run individual analyses
sig_result = detector.analyze_signature(check, signatures)
wm_result = detector.detect_watermark(check, watermark_desc)
tamp_result = detector.detect_tampering(check, focus_areas)

# Or run comprehensive analysis
full_result = detector.comprehensive_fraud_analysis(
    primary_check=check,
    comparison_signatures=signatures,
    expected_watermark=watermark_desc,
    focus_areas=["amount", "payee", "date"]
)
```

### Integration with ADK

The fraud detection tool is fully integrated with the ADK platform:

```yaml
# In your agent configuration
tools:
  - image_fraud_detector

# The tool will be automatically loaded and available
```

## Resources

- **Main Documentation**: `FRAUD_DETECTION_README.md`
- **Tool Configuration**: `data/tools/image-fraud-detector.yaml`
- **Agent Configs**: `data/agents/fraud-*-agent.yaml`
- **Graph Workflow**: `data/graphs/fraud-detection-voting.yaml`
- **Example Code**: `examples/fraud_detection_example.py`
- **Test Suite**: `test_fraud_detection.py`

---

**Ready to detect fraud? Start with the test suite!**

```bash
python test_fraud_detection.py
```

# Image Analysis Tool - Quick Start Guide

## Overview

The **Image Analysis Tool** is a versatile tool that provides 7 different types of image analysis capabilities through a simple API.

## Quick Test

### 1. Verify Tool is Available

```bash
curl http://localhost:8100/tools/image_analysis
```

### 2. Run a Simple Test (Mock Mode)

```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/any/path/test.jpg",
      "analysis_type": "general"
    },
    "mock": true
  }'
```

### 3. Analyze a Real Image

```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "d:/ds/work/workspace/git/dsp-adk/data/fraud_detection/sample_checks/check_001.jpg",
      "analysis_type": "general"
    },
    "mock": false
  }'
```

## Analysis Types

| Type | Description | Use Case |
|------|-------------|----------|
| `general` | Basic info (size, format, dimensions) | Quick image validation |
| `object_detection` | Detect objects with bounding boxes | Security, inventory |
| `text_extraction` | OCR text extraction | Document processing |
| `face_detection` | Detect faces and landmarks | Identity verification |
| `image_classification` | Categorize images | Content organization |
| `color_analysis` | Dominant colors and palette | Design, branding |
| `quality_assessment` | Quality metrics (blur, noise) | Quality control |

## Postman Collection

Import `postman_image_analysis.json` into Postman for ready-to-use requests.

## Test Script

Run the automated test suite:

```bash
python test_image_analysis_tool.py
```

This will verify:
- ✓ Tool is registered
- ✓ Schema is valid
- ✓ All 7 analysis types work
- ✓ Tool appears in tool list

## Files Created

1. **`data/tools/image_analysis.yaml`** - Tool configuration
2. **`app/tools/image_analysis.py`** - Python implementation
3. **`postman_image_analysis.json`** - Postman collection (11 requests)
4. **`IMAGE_ANALYSIS_TOOL.md`** - Complete documentation
5. **`test_image_analysis_tool.py`** - Automated test suite
6. **`IMAGE_ANALYSIS_QUICKSTART.md`** - This file

## Example Responses

### General Analysis
```json
{
  "success": true,
  "analysis_type": "general",
  "results": {
    "image_format": "JPEG",
    "dimensions": {"width": 1920, "height": 1080},
    "aspect_ratio": 1.78,
    "file_size_kb": 245.6,
    "megapixels": 2.07
  }
}
```

### Object Detection
```json
{
  "success": true,
  "analysis_type": "object_detection",
  "results": {
    "objects_detected": [
      {"label": "person", "confidence": 0.95},
      {"label": "car", "confidence": 0.88}
    ],
    "total_objects": 2
  }
}
```

## Integration with Agents

Use the tool in agent workflows:

```yaml
# In agent configuration
tools:
  - image_analysis

# Agent can call:
# "Analyze the image at /path/to/image.jpg for objects"
```

## Production Notes

Current implementation uses **mock data** for advanced analysis types. To use in production:

1. Integrate with vision AI services (Azure, AWS, Google Cloud)
2. Update implementation in `app/tools/image_analysis.py`
3. Add API keys to environment variables
4. Test with real images

See `IMAGE_ANALYSIS_TOOL.md` for detailed integration examples.

## Support

- Full documentation: `IMAGE_ANALYSIS_TOOL.md`
- Postman examples: `postman_image_analysis.json`
- Test suite: `test_image_analysis_tool.py`

## Next Steps

1. **Test the tool**: Run `python test_image_analysis_tool.py`
2. **Try Postman**: Import the collection and test different analysis types
3. **Integrate with agents**: Add to your agent's tool list
4. **Production setup**: Connect to real vision AI services

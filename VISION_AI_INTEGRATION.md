# Vision AI Integration Guide

The Image Analysis Tool now supports **real vision AI providers** in addition to mock mode:

- ✅ **Azure Computer Vision** - Microsoft's vision AI service
- ✅ **AWS Rekognition** - Amazon's image analysis service  
- ✅ **Google Cloud Vision** - Google's vision AI platform
- ✅ **Mock Mode** - Default testing mode (no API keys required)

## Quick Start

### 1. Choose Your Provider

Edit `data/tools/image_analysis.yaml` and configure your provider:

```yaml
vision_ai:
  provider: azure  # or "aws", "google", "mock"
  
  # Add provider-specific settings (see below)
```

### 2. Install Dependencies

```bash
# For Azure
pip install azure-cognitiveservices-vision-computervision azure-ai-vision-imageanalysis

# For AWS
pip install boto3

# For Google Cloud
pip install google-cloud-vision
```

### 3. Set Environment Variables

```bash
# Azure
export AZURE_VISION_API_KEY="your-key-here"

# AWS
export AWS_ACCESS_KEY_ID="your-key-here"
export AWS_SECRET_ACCESS_KEY="your-secret-here"

# Google
export GOOGLE_CLOUD_API_KEY="your-key-here"
```

### 4. Test It

```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/image.jpg",
      "analysis_type": "object_detection"
    },
    "mock": false
  }'
```

---

## Provider Configuration

### Azure Computer Vision

**Configuration:**

```yaml
vision_ai:
  provider: azure
  azure_endpoint: "https://YOUR_RESOURCE.cognitiveservices.azure.com/"
  azure_api_key: "${AZURE_VISION_API_KEY}"
  azure_api_version: "2023-10-01"
  azure_face_endpoint: "https://YOUR_FACE_RESOURCE.cognitiveservices.azure.com/"  # Optional for face detection
```

**Setup Steps:**

1. Create Azure Computer Vision resource in Azure Portal
2. Get endpoint URL and API key from resource
3. For face detection, create separate Face API resource (optional)
4. Set environment variable: `AZURE_VISION_API_KEY`

**Supported Analysis Types:**
- ✅ general
- ✅ object_detection
- ✅ text_extraction (OCR)
- ✅ face_detection (requires Face API)
- ✅ image_classification
- ✅ color_analysis
- ✅ quality_assessment

**Pricing:** [Azure Computer Vision Pricing](https://azure.microsoft.com/pricing/details/cognitive-services/computer-vision/)

---

### AWS Rekognition

**Configuration:**

```yaml
vision_ai:
  provider: aws
  aws_region: "us-east-1"
  aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
  aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
```

**Setup Steps:**

1. Create AWS account and enable Rekognition
2. Create IAM user with Rekognition permissions
3. Get access key ID and secret access key
4. Set environment variables: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`

**Supported Analysis Types:**
- ✅ general
- ✅ object_detection
- ✅ text_extraction
- ✅ face_detection
- ✅ image_classification
- ❌ color_analysis (not supported)
- ❌ quality_assessment (not supported)

**Pricing:** [AWS Rekognition Pricing](https://aws.amazon.com/rekognition/pricing/)

---

### Google Cloud Vision

**Configuration:**

```yaml
vision_ai:
  provider: google
  google_api_key: "${GOOGLE_CLOUD_API_KEY}"
  google_project_id: "your-project-id"  # Optional
```

**Setup Steps:**

1. Create Google Cloud project
2. Enable Cloud Vision API
3. Create API key in Credentials
4. Set environment variable: `GOOGLE_CLOUD_API_KEY`

**Supported Analysis Types:**
- ✅ general
- ✅ object_detection
- ✅ text_extraction
- ✅ face_detection
- ✅ image_classification
- ❌ color_analysis (not supported)
- ❌ quality_assessment (not supported)

**Pricing:** [Google Cloud Vision Pricing](https://cloud.google.com/vision/pricing)

---

## Configuration Examples

### Example 1: Azure with Environment Variables

```yaml
# data/tools/image_analysis.yaml
vision_ai:
  provider: azure
  azure_endpoint: "https://myresource.cognitiveservices.azure.com/"
  azure_api_key: "${AZURE_VISION_API_KEY}"
  azure_api_version: "2023-10-01"
```

```bash
# .env file
AZURE_VISION_API_KEY=abc123def456...
```

### Example 2: AWS with Multiple Regions

```yaml
# For US East
vision_ai:
  provider: aws
  aws_region: "us-east-1"
  aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
  aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
```

### Example 3: Google Cloud

```yaml
vision_ai:
  provider: google
  google_api_key: "${GOOGLE_CLOUD_API_KEY}"
  google_project_id: "my-ai-project"
```

### Example 4: Mock Mode (Default)

```yaml
vision_ai:
  provider: mock
  # No API keys needed - returns simulated data
```

---

## API Request Examples

### Using Azure

```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/image.jpg",
      "analysis_type": "object_detection",
      "options": {
        "confidence_threshold": 0.7,
        "max_objects": 10
      }
    },
    "mock": false
  }'
```

### Using Base64 Image Data

```bash
# Encode image
IMAGE_BASE64=$(python -c "import base64; print(base64.b64encode(open('image.jpg','rb').read()).decode())")

# Send request
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"arguments\": {
      \"image_data\": \"$IMAGE_BASE64\",
      \"analysis_type\": \"text_extraction\"
    },
    \"mock\": false
  }"
```

### Response Format

```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "object_detection",
    "image_source": "/path/to/image.jpg",
    "results": {
      "objects_detected": [
        {
          "label": "person",
          "confidence": 0.95,
          "bounding_box": {"left": 0.1, "top": 0.2, "width": 0.3, "height": 0.5}
        },
        {
          "label": "car",
          "confidence": 0.88,
          "bounding_box": {"left": 0.5, "top": 0.6, "width": 0.4, "height": 0.3}
        }
      ],
      "total_objects": 2,
      "confidence_threshold": 0.7,
      "provider": "azure_computer_vision"
    },
    "metadata": {
      "format": "JPEG",
      "mode": "RGB",
      "width": 1920,
      "height": 1080,
      "size_bytes": 245678
    }
  }
}
```

---

## Analysis Type Details

### 1. General Analysis

**What it does:** Basic image information and description

**Azure Response:**
```json
{
  "image_format": "JPEG",
  "dimensions": {"width": 1920, "height": 1080},
  "description": "A person standing next to a car",
  "tags": ["person", "car", "outdoor", "street"],
  "is_clip_art": false,
  "is_line_drawing": false
}
```

### 2. Object Detection

**What it does:** Detects and localizes objects with bounding boxes

**Options:**
- `confidence_threshold`: Minimum confidence (0.0-1.0)
- `max_objects`: Maximum objects to return

**Azure Response:**
```json
{
  "objects_detected": [
    {
      "label": "person",
      "confidence": 0.95,
      "bounding_box": {"left": 100, "top": 200, "width": 300, "height": 500}
    }
  ],
  "total_objects": 1,
  "provider": "azure_computer_vision"
}
```

### 3. Text Extraction (OCR)

**What it does:** Extracts text from images

**Options:**
- `language`: Language code (e.g., "en", "es", "fr")

**Azure Response:**
```json
{
  "text_blocks": [
    {
      "text": "Hello World",
      "confidence": 0.98,
      "bounding_box": [100, 200, 300, 200, 300, 250, 100, 250]
    }
  ],
  "full_text": "Hello World\nWelcome to AI",
  "total_blocks": 2,
  "provider": "azure_computer_vision"
}
```

### 4. Face Detection

**What it does:** Detects faces and facial attributes

**Options:**
- `return_landmarks`: Include facial landmarks (default: true)

**Azure Response:**
```json
{
  "faces_detected": [
    {
      "face_id": "abc-123-def",
      "bounding_box": {"left": 100, "top": 150, "width": 200, "height": 250},
      "attributes": {
        "age": 32,
        "gender": {"gender": "male", "confidence": 0.99},
        "emotion": {"happiness": 0.85, "neutral": 0.10},
        "smile": {"value": 0.80},
        "glasses": {"value": "NoGlasses"}
      },
      "landmarks": {...}
    }
  ],
  "total_faces": 1,
  "provider": "azure_face_api"
}
```

### 5. Image Classification

**What it does:** Categorizes and tags images

**Azure Response:**
```json
{
  "categories": [
    {"name": "outdoor_", "confidence": 0.92},
    {"name": "people_", "confidence": 0.85}
  ],
  "tags": [
    {"name": "person", "confidence": 0.95},
    {"name": "outdoor", "confidence": 0.90}
  ],
  "primary_category": "outdoor_",
  "provider": "azure_computer_vision"
}
```

### 6. Color Analysis

**What it does:** Analyzes dominant colors

**Azure Response:**
```json
{
  "dominant_color_foreground": "Black",
  "dominant_color_background": "White",
  "dominant_colors": ["Black", "White", "Grey"],
  "accent_color": "FF5733",
  "is_bw_image": false,
  "provider": "azure_computer_vision"
}
```

### 7. Quality Assessment

**What it does:** Assesses image quality metrics

**Azure Response:**
```json
{
  "resolution": "1920x1080",
  "megapixels": 2.07,
  "is_clip_art": false,
  "is_line_drawing": false,
  "format": "JPEG",
  "file_size_kb": 245.6,
  "provider": "azure_computer_vision"
}
```

---

## Error Handling

### Common Errors

**1. Missing API Key**
```json
{
  "success": false,
  "error": "Azure endpoint and API key are required",
  "provider": "azure"
}
```

**2. Invalid Credentials**
```json
{
  "success": false,
  "error": "Access denied. Check your API key.",
  "provider": "azure"
}
```

**3. Rate Limit Exceeded**
```json
{
  "success": false,
  "error": "Rate limit exceeded. Please try again later.",
  "provider": "aws"
}
```

**4. Unsupported Analysis Type**
```json
{
  "success": false,
  "error": "Analysis type 'color_analysis' not supported by AWS Rekognition",
  "provider": "aws"
}
```

---

## Cost Optimization Tips

### 1. Use Mock Mode for Development
```yaml
vision_ai:
  provider: mock  # Free, no API calls
```

### 2. Set Confidence Thresholds
```json
{
  "options": {
    "confidence_threshold": 0.8  // Higher = fewer results = lower cost
  }
}
```

### 3. Limit Results
```json
{
  "options": {
    "max_objects": 5  // Limit number of objects detected
  }
}
```

### 4. Choose the Right Provider

| Feature | Azure | AWS | Google | Cost |
|---------|-------|-----|--------|------|
| Object Detection | ✅ | ✅ | ✅ | $$$ |
| OCR | ✅ | ✅ | ✅ | $$ |
| Face Detection | ✅ | ✅ | ✅ | $$$ |
| Color Analysis | ✅ | ❌ | ❌ | $ |

### 5. Batch Processing

Process multiple images in a single session to optimize API usage.

---

## Security Best Practices

### 1. Use Environment Variables

❌ **Don't:**
```yaml
azure_api_key: "abc123def456..."  # Hardcoded
```

✅ **Do:**
```yaml
azure_api_key: "${AZURE_VISION_API_KEY}"  # From environment
```

### 2. Rotate API Keys Regularly

Set up key rotation policies in your cloud provider.

### 3. Use Least Privilege IAM

For AWS, create IAM users with only Rekognition permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "rekognition:DetectLabels",
      "rekognition:DetectText",
      "rekognition:DetectFaces"
    ],
    "Resource": "*"
  }]
}
```

### 4. Monitor API Usage

Set up alerts for unusual API usage patterns.

---

## Troubleshooting

### Issue: "Module not found" error

**Solution:** Install the required provider SDK:
```bash
pip install azure-cognitiveservices-vision-computervision  # Azure
pip install boto3  # AWS
pip install google-cloud-vision  # Google
```

### Issue: "Failed to decode base64 image data"

**Solution:** Ensure base64 string is valid and remove data URL prefix:
```python
# Remove "data:image/jpeg;base64," prefix
image_data = image_data.split(',', 1)[1]
```

### Issue: Azure OCR timeout

**Solution:** Increase timeout in tool configuration:
```yaml
timeout: 60  # Increase from default 30 seconds
```

### Issue: AWS credentials not found

**Solution:** Configure AWS credentials:
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."
```

---

## Migration from Mock to Real API

### Step 1: Test with Mock Mode

```yaml
vision_ai:
  provider: mock
```

### Step 2: Set Up Provider Account

Choose Azure, AWS, or Google and create account.

### Step 3: Update Configuration

```yaml
vision_ai:
  provider: azure  # Change from mock
  azure_endpoint: "https://..."
  azure_api_key: "${AZURE_VISION_API_KEY}"
```

### Step 4: Install Dependencies

```bash
pip install azure-cognitiveservices-vision-computervision
```

### Step 5: Test with Real Images

Start with a few test images before production use.

### Step 6: Monitor Costs

Set up billing alerts in your cloud provider console.

---

## Performance Comparison

| Provider | Avg Latency | Accuracy | Features | Cost |
|----------|-------------|----------|----------|------|
| **Azure** | ~1-2s | ⭐⭐⭐⭐⭐ | Most comprehensive | $$$ |
| **AWS** | ~0.5-1s | ⭐⭐⭐⭐ | Fast, reliable | $$ |
| **Google** | ~1-1.5s | ⭐⭐⭐⭐⭐ | Excellent OCR | $$$ |
| **Mock** | ~0.1s | N/A | Testing only | Free |

---

## Support

- **Azure:** [Azure Support](https://azure.microsoft.com/support/)
- **AWS:** [AWS Support](https://aws.amazon.com/support/)
- **Google:** [Google Cloud Support](https://cloud.google.com/support)

## Additional Resources

- [Azure Computer Vision Docs](https://learn.microsoft.com/azure/cognitive-services/computer-vision/)
- [AWS Rekognition Docs](https://docs.aws.amazon.com/rekognition/)
- [Google Cloud Vision Docs](https://cloud.google.com/vision/docs)

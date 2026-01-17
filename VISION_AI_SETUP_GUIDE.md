# Vision AI Setup Guide - Quick Reference

This guide helps you quickly set up real vision AI providers for the Image Analysis Tool.

## 🚀 Quick Setup

### Option 1: Azure Computer Vision (Recommended)

**1. Create Azure Resource**
- Go to [Azure Portal](https://portal.azure.com)
- Create new "Computer Vision" resource
- Choose pricing tier (F0 for free tier, S1 for production)

**2. Get Credentials**
```bash
# From Azure Portal, copy:
Endpoint: https://YOUR_RESOURCE.cognitiveservices.azure.com/
Key: abc123def456...
```

**3. Configure Tool**
```bash
# Copy example configuration
cp data/tools/image_analysis_azure_example.yaml data/tools/image_analysis.yaml

# Edit the file and update:
# - azure_endpoint with your endpoint URL
```

**4. Set Environment Variable**
```bash
# Linux/Mac
export AZURE_VISION_API_KEY="your-key-here"

# Windows PowerShell
$env:AZURE_VISION_API_KEY="your-key-here"

# Or add to .env file
echo "AZURE_VISION_API_KEY=your-key-here" >> .env
```

**5. Install Dependencies**
```bash
pip install azure-cognitiveservices-vision-computervision azure-ai-vision-imageanalysis
```

**6. Test**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/test.jpg",
      "analysis_type": "general"
    },
    "mock": false
  }'
```

---

### Option 2: AWS Rekognition

**1. Create AWS Account**
- Sign up at [AWS Console](https://aws.amazon.com)
- Enable Rekognition service

**2. Create IAM User**
```bash
# In AWS Console:
1. Go to IAM → Users → Create User
2. Attach policy: AmazonRekognitionFullAccess
3. Create access key
4. Save Access Key ID and Secret Access Key
```

**3. Configure Tool**
```bash
cp data/tools/image_analysis_aws_example.yaml data/tools/image_analysis.yaml
```

**4. Set Environment Variables**
```bash
export AWS_ACCESS_KEY_ID="AKIA..."
export AWS_SECRET_ACCESS_KEY="secret..."
export AWS_DEFAULT_REGION="us-east-1"
```

**5. Install Dependencies**
```bash
pip install boto3
```

**6. Test**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/test.jpg",
      "analysis_type": "object_detection"
    }
  }'
```

---

### Option 3: Google Cloud Vision

**1. Create Google Cloud Project**
- Go to [Google Cloud Console](https://console.cloud.google.com)
- Create new project
- Enable "Cloud Vision API"

**2. Create API Key**
```bash
# In Google Cloud Console:
1. Go to APIs & Services → Credentials
2. Create Credentials → API Key
3. Copy the API key
```

**3. Configure Tool**
```yaml
# Edit data/tools/image_analysis.yaml
vision_ai:
  provider: google
  google_api_key: "${GOOGLE_CLOUD_API_KEY}"
  google_project_id: "your-project-id"
```

**4. Set Environment Variable**
```bash
export GOOGLE_CLOUD_API_KEY="your-api-key"
```

**5. Install Dependencies**
```bash
pip install google-cloud-vision
```

**6. Test**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/test.jpg",
      "analysis_type": "text_extraction"
    }
  }'
```

---

## 📋 Feature Comparison

| Feature | Azure | AWS | Google | Mock |
|---------|-------|-----|--------|------|
| **General Analysis** | ✅ | ✅ | ✅ | ✅ |
| **Object Detection** | ✅ | ✅ | ✅ | ✅ |
| **Text Extraction (OCR)** | ✅ | ✅ | ✅ | ✅ |
| **Face Detection** | ✅ | ✅ | ✅ | ✅ |
| **Image Classification** | ✅ | ✅ | ✅ | ✅ |
| **Color Analysis** | ✅ | ❌ | ❌ | ✅ |
| **Quality Assessment** | ✅ | ❌ | ❌ | ✅ |
| **Free Tier** | ✅ 5K/month | ✅ 5K/month | ✅ 1K/month | ✅ Unlimited |
| **Pricing** | $$$ | $$ | $$$ | Free |
| **Setup Complexity** | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐ |

---

## 🔧 Configuration Files

### Mock Mode (Default - No Setup Required)
```yaml
# data/tools/image_analysis.yaml
vision_ai:
  provider: mock
```

### Azure Configuration
```yaml
vision_ai:
  provider: azure
  azure_endpoint: "https://YOUR_RESOURCE.cognitiveservices.azure.com/"
  azure_api_key: "${AZURE_VISION_API_KEY}"
  azure_api_version: "2023-10-01"
```

### AWS Configuration
```yaml
vision_ai:
  provider: aws
  aws_region: "us-east-1"
  aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
  aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
```

### Google Configuration
```yaml
vision_ai:
  provider: google
  google_api_key: "${GOOGLE_CLOUD_API_KEY}"
  google_project_id: "your-project-id"
```

---

## 🧪 Testing Your Setup

### Test Script

Create `test_vision_ai.py`:

```python
import requests
import base64

# Read and encode test image
with open('test_image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Test request
response = requests.post(
    'http://localhost:8100/tools/image_analysis/execute',
    json={
        'arguments': {
            'image_data': image_data,
            'analysis_type': 'general'
        },
        'mock': False
    }
)

result = response.json()
print(f"Success: {result['result']['success']}")
print(f"Provider: {result['result']['results'].get('provider', 'mock')}")
print(f"Results: {result['result']['results']}")
```

Run:
```bash
python test_vision_ai.py
```

### Expected Output

**Mock Mode:**
```json
{
  "success": true,
  "results": {
    "image_format": "JPEG",
    "note": "This is a mock implementation"
  }
}
```

**Real Provider (Azure):**
```json
{
  "success": true,
  "results": {
    "image_format": "JPEG",
    "description": "A person standing next to a car",
    "tags": ["person", "car", "outdoor"],
    "provider": "azure_computer_vision"
  }
}
```

---

## ⚠️ Troubleshooting

### Error: "Azure endpoint and API key are required"

**Solution:**
1. Check environment variable is set: `echo $AZURE_VISION_API_KEY`
2. Verify configuration in `image_analysis.yaml`
3. Restart the server after setting environment variables

### Error: "Module 'azure.cognitiveservices.vision' not found"

**Solution:**
```bash
pip install azure-cognitiveservices-vision-computervision
```

### Error: "Access denied" or "401 Unauthorized"

**Solution:**
1. Verify API key is correct
2. Check endpoint URL matches your resource
3. Ensure resource is active in cloud console

### Error: "Rate limit exceeded"

**Solution:**
1. Wait a few minutes
2. Upgrade to paid tier
3. Implement request throttling in your application

---

## 💰 Cost Estimates

### Azure Computer Vision
- **Free Tier:** 5,000 transactions/month
- **Standard:** $1.00 per 1,000 transactions
- **Face API:** $1.00 per 1,000 transactions

### AWS Rekognition
- **Free Tier:** 5,000 images/month (first year)
- **Standard:** $1.00 per 1,000 images

### Google Cloud Vision
- **Free Tier:** 1,000 units/month
- **Standard:** $1.50 per 1,000 images

### Cost Optimization
```yaml
# Limit analysis frequency
rate_limit: 10  # Max 10 requests per minute

# Use mock mode for development
vision_ai:
  provider: mock  # Switch to real provider only in production
```

---

## 🔐 Security Checklist

- [ ] API keys stored in environment variables (not hardcoded)
- [ ] `.env` file added to `.gitignore`
- [ ] IAM permissions follow least privilege principle
- [ ] API key rotation policy in place
- [ ] Rate limiting configured
- [ ] Billing alerts set up in cloud console
- [ ] HTTPS used for all API calls
- [ ] Logs don't expose sensitive data

---

## 📚 Next Steps

1. **Start with Mock Mode** - Test functionality without API costs
2. **Choose Provider** - Based on features and pricing
3. **Set Up Free Tier** - Test with real API in free tier
4. **Monitor Usage** - Track API calls and costs
5. **Scale to Production** - Upgrade when ready

## 🆘 Support Resources

- **Azure:** [Azure Support](https://azure.microsoft.com/support/)
- **AWS:** [AWS Support Center](https://console.aws.amazon.com/support/)
- **Google:** [Google Cloud Support](https://cloud.google.com/support)
- **ADK Issues:** [GitHub Issues](https://github.com/your-repo/dsp-adk/issues)

---

## 📖 Related Documentation

- [VISION_AI_INTEGRATION.md](VISION_AI_INTEGRATION.md) - Detailed integration guide
- [IMAGE_ANALYSIS_TOOL.md](IMAGE_ANALYSIS_TOOL.md) - Tool documentation
- [POSTMAN_IMAGE_UPLOAD_GUIDE.md](POSTMAN_IMAGE_UPLOAD_GUIDE.md) - Testing guide

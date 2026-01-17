# Image Fraud Detector Tool - API Examples

## Tool Overview

**Tool ID:** `image_fraud_detector`  
**Endpoint:** `POST /tools/image_fraud_detector/execute`  
**Authentication:** Not required (jwt_required: false)

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `action` | string (enum) | Yes | Type of fraud analysis: `analyze_signature`, `detect_watermark`, `detect_tampering`, `comprehensive_analysis` |
| `primary_check` | string | Yes | Path to the primary check image being analyzed |
| `comparison_signatures` | array[string] | No | Paths to known valid signature samples for comparison |
| `expected_watermark` | string | No | Description of expected watermark on the check |
| `focus_areas` | array[string] | No | Specific areas to focus tampering detection on (e.g., amount, payee, date) |

## Request Format

```json
{
  "arguments": {
    "action": "<action_type>",
    "primary_check": "<path_to_check_image>",
    "comparison_signatures": ["<path1>", "<path2>"],
    "expected_watermark": "<watermark_description>",
    "focus_areas": ["amount", "payee", "date"]
  },
  "mock": false
}
```

## Examples

### 1. Comprehensive Analysis

Performs all fraud detection checks on a check image.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_fraud_detector/execute" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{
    "arguments": {
      "action": "comprehensive_analysis",
      "primary_check": "/path/to/check_image.jpg",
      "comparison_signatures": [
        "/path/to/signature1.jpg",
        "/path/to/signature2.jpg"
      ],
      "expected_watermark": "VOID",
      "focus_areas": ["amount", "payee", "date"]
    },
    "mock": false
  }'
```

**PowerShell:**
```powershell
$body = @{
    arguments = @{
        action = "comprehensive_analysis"
        primary_check = "/path/to/check_image.jpg"
        comparison_signatures = @(
            "/path/to/signature1.jpg",
            "/path/to/signature2.jpg"
        )
        expected_watermark = "VOID"
        focus_areas = @("amount", "payee", "date")
    }
    mock = $false
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Uri "http://localhost:8100/tools/image_fraud_detector/execute" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

### 2. Signature Analysis Only

Compares signature on check against known valid signatures.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_fraud_detector/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "action": "analyze_signature",
      "primary_check": "/path/to/check_image.jpg",
      "comparison_signatures": [
        "/path/to/known_signature1.jpg",
        "/path/to/known_signature2.jpg"
      ]
    },
    "mock": false
  }'
```

### 3. Watermark Detection

Detects presence of expected watermark on check.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_fraud_detector/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "action": "detect_watermark",
      "primary_check": "/path/to/check_image.jpg",
      "expected_watermark": "VOID"
    },
    "mock": false
  }'
```

### 4. Tampering Detection

Detects signs of tampering in specific areas of the check.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_fraud_detector/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "action": "detect_tampering",
      "primary_check": "/path/to/check_image.jpg",
      "focus_areas": ["amount", "payee"]
    },
    "mock": false
  }'
```

### 5. Mock Mode (Testing)

Execute in mock mode for testing without actual execution.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_fraud_detector/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "action": "comprehensive_analysis",
      "primary_check": "/path/to/check_image.jpg",
      "comparison_signatures": ["/path/to/signature1.jpg"],
      "expected_watermark": "VOID",
      "focus_areas": ["amount"]
    },
    "mock": true
  }'
```

## Response Format

**Success Response:**
```json
{
  "success": true,
  "tool_id": "image_fraud_detector",
  "result": {
    "analysis_type": "comprehensive_analysis",
    "fraud_detected": false,
    "confidence_score": 0.95,
    "details": {
      "signature_match": true,
      "watermark_present": true,
      "tampering_detected": false
    }
  },
  "error": null
}
```

**Error Response:**
```json
{
  "success": false,
  "tool_id": "image_fraud_detector",
  "result": {},
  "error": "Error message describing what went wrong"
}
```

## Additional Endpoints

### Get Tool Configuration
```bash
curl -X GET "http://localhost:8100/tools/image_fraud_detector" \
  -H "Accept: application/json"
```

### Get Tool Schema (OpenAI-compatible)
```bash
curl -X GET "http://localhost:8100/tools/image_fraud_detector/schema" \
  -H "Accept: application/json"
```

### List All Tools
```bash
curl -X GET "http://localhost:8100/tools" \
  -H "Accept: application/json"
```

## Postman Collection

Import the Postman collection from `postman_image_fraud_detector.json` for ready-to-use requests.

## Notes

- The tool does not require JWT authentication (`jwt_required: false`)
- Timeout is set to 30 seconds
- No retry attempts on failure (`retry_count: 0`)
- Use `mock: true` for testing without actual execution
- Image paths should be accessible to the server

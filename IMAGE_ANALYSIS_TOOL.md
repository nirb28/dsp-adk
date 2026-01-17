# Image Analysis Tool - API Documentation

## Overview

**Tool ID:** `image_analysis`  
**Endpoint:** `POST /tools/image_analysis/execute`  
**Authentication:** Not required (jwt_required: false)  
**Timeout:** 30 seconds  
**Rate Limit:** 50 requests per minute

## Description

General-purpose image analysis tool that can perform various types of analysis on images including object detection, text extraction, face detection, image classification, color analysis, and quality assessment.

## Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `image_path` | string | **Yes** | - | Path to the image file (local file path or URL) |
| `analysis_type` | string (enum) | No | `general` | Type of analysis to perform |
| `options` | object | No | `{}` | Additional options specific to the analysis type |

### Analysis Types

- **`general`** - Basic image information (dimensions, format, size, aspect ratio)
- **`object_detection`** - Detect and identify objects in the image
- **`text_extraction`** - Extract text from the image (OCR)
- **`face_detection`** - Detect faces and facial features
- **`image_classification`** - Classify the image into categories
- **`color_analysis`** - Analyze dominant colors and color distribution
- **`quality_assessment`** - Assess image quality (blur, brightness, contrast)

## Request Format

```json
{
  "arguments": {
    "image_path": "<path_or_url>",
    "analysis_type": "<analysis_type>",
    "options": {
      // Optional analysis-specific options
    }
  },
  "mock": false
}
```

## Examples

### 1. General Analysis (Default)

Get basic image information including dimensions, format, and file size.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "d:/images/photo.jpg",
      "analysis_type": "general"
    },
    "mock": false
  }'
```

**PowerShell:**
```powershell
$body = @{
    arguments = @{
        image_path = "d:/images/photo.jpg"
        analysis_type = "general"
    }
    mock = $false
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8100/tools/image_analysis/execute" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "general",
    "image_path": "d:/images/photo.jpg",
    "results": {
      "image_format": "JPEG",
      "color_mode": "RGB",
      "dimensions": {
        "width": 1920,
        "height": 1080
      },
      "aspect_ratio": 1.78,
      "file_size_kb": 245.6,
      "megapixels": 2.07
    },
    "metadata": {
      "format": "JPEG",
      "mode": "RGB",
      "width": 1920,
      "height": 1080,
      "size_bytes": 251494
    }
  },
  "error": null
}
```

### 2. Object Detection

Detect and identify objects in the image with bounding boxes.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/street_scene.jpg",
      "analysis_type": "object_detection",
      "options": {
        "confidence_threshold": 0.5,
        "max_objects": 10
      }
    },
    "mock": false
  }'
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "object_detection",
    "results": {
      "objects_detected": [
        {
          "label": "person",
          "confidence": 0.95,
          "bounding_box": {"x": 100, "y": 150, "width": 200, "height": 400}
        },
        {
          "label": "car",
          "confidence": 0.88,
          "bounding_box": {"x": 400, "y": 300, "width": 300, "height": 200}
        }
      ],
      "total_objects": 2,
      "detection_model": "mock-detector-v1"
    }
  }
}
```

### 3. Text Extraction (OCR)

Extract text from documents, signs, or any image containing text.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/document.jpg",
      "analysis_type": "text_extraction",
      "options": {
        "language": "en"
      }
    },
    "mock": false
  }'
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "text_extraction",
    "results": {
      "text_found": true,
      "extracted_text": "Sample extracted text from image",
      "text_regions": [
        {
          "text": "Sample text",
          "confidence": 0.92,
          "bounding_box": {"x": 50, "y": 100, "width": 300, "height": 50}
        }
      ],
      "language_detected": "en",
      "ocr_engine": "mock-ocr-v1"
    }
  }
}
```

### 4. Face Detection

Detect faces and facial landmarks in photos.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/portrait.jpg",
      "analysis_type": "face_detection",
      "options": {
        "detect_landmarks": true,
        "detect_attributes": true
      }
    },
    "mock": false
  }'
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "face_detection",
    "results": {
      "faces_detected": 1,
      "faces": [
        {
          "confidence": 0.97,
          "bounding_box": {"x": 200, "y": 150, "width": 150, "height": 200},
          "landmarks": {
            "left_eye": {"x": 230, "y": 200},
            "right_eye": {"x": 320, "y": 200},
            "nose": {"x": 275, "y": 250},
            "mouth": {"x": 275, "y": 300}
          },
          "attributes": {
            "age_estimate": "25-35",
            "gender": "unknown",
            "emotion": "neutral"
          }
        }
      ]
    }
  }
}
```

### 5. Image Classification

Classify images into categories.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/landscape.jpg",
      "analysis_type": "image_classification",
      "options": {
        "top_k": 5
      }
    },
    "mock": false
  }'
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "image_classification",
    "results": {
      "top_predictions": [
        {"label": "landscape", "confidence": 0.85},
        {"label": "outdoor", "confidence": 0.78},
        {"label": "nature", "confidence": 0.72}
      ],
      "primary_category": "landscape"
    }
  }
}
```

### 6. Color Analysis

Analyze dominant colors and color distribution in images.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/artwork.jpg",
      "analysis_type": "color_analysis",
      "options": {
        "num_colors": 5
      }
    },
    "mock": false
  }'
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "color_analysis",
    "results": {
      "dominant_colors": [
        {"color": "#3A5F8B", "percentage": 35.2, "name": "blue"},
        {"color": "#8BC34A", "percentage": 28.5, "name": "green"},
        {"color": "#FFFFFF", "percentage": 20.1, "name": "white"}
      ],
      "color_palette": ["#3A5F8B", "#8BC34A", "#FFFFFF", "#FF5722", "#9E9E9E"],
      "average_brightness": 0.65,
      "color_diversity_score": 0.72
    }
  }
}
```

### 7. Quality Assessment

Assess image quality including sharpness, brightness, and noise.

**cURL:**
```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_path": "/path/to/photo.jpg",
      "analysis_type": "quality_assessment"
    },
    "mock": false
  }'
```

**Response:**
```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "quality_assessment",
    "results": {
      "overall_quality_score": 0.82,
      "metrics": {
        "sharpness": 0.85,
        "brightness": 0.75,
        "contrast": 0.80,
        "noise_level": 0.15,
        "blur_detected": false
      },
      "recommendations": [
        "Image quality is good",
        "Slight increase in contrast could improve visibility"
      ],
      "is_suitable_for_analysis": true
    }
  }
}
```

## Error Handling

**Error Response:**
```json
{
  "success": false,
  "tool_id": "image_analysis",
  "result": {
    "success": false,
    "error": "Image file not found: /path/to/image.jpg"
  },
  "error": "Image file not found: /path/to/image.jpg"
}
```

## Additional Endpoints

### Get Tool Configuration
```bash
curl -X GET "http://localhost:8100/tools/image_analysis"
```

### Get Tool Schema (OpenAI-compatible)
```bash
curl -X GET "http://localhost:8100/tools/image_analysis/schema"
```

### List All Tools
```bash
curl -X GET "http://localhost:8100/tools"
```

## Postman Collection

Import the Postman collection from `postman_image_analysis.json` for ready-to-use requests with all analysis types.

## Integration Notes

### Current Implementation
The tool currently provides **mock implementations** for advanced analysis types (object detection, OCR, face detection, etc.). These return sample data for testing and development.

### Production Integration
To use in production, integrate with actual vision AI services:

- **Object Detection**: Azure Computer Vision, AWS Rekognition, Google Cloud Vision
- **Text Extraction**: Tesseract OCR, Azure OCR, Google Cloud Vision OCR
- **Face Detection**: Azure Face API, AWS Rekognition, Google Cloud Vision
- **Classification**: Custom ML models, Azure Custom Vision, AWS Rekognition
- **Color Analysis**: PIL/Pillow color quantization, ColorThief library
- **Quality Assessment**: OpenCV quality metrics, custom algorithms

### Example Production Integration

```python
# In app/tools/image_analysis.py
import requests

def _analyze_object_detection_production(image_path, options):
    # Example: Azure Computer Vision
    endpoint = "https://your-resource.cognitiveservices.azure.com/"
    api_key = os.getenv("AZURE_VISION_API_KEY")
    
    with open(image_path, 'rb') as image_file:
        response = requests.post(
            f"{endpoint}/vision/v3.2/detect",
            headers={"Ocp-Apim-Subscription-Key": api_key},
            files={"image": image_file}
        )
    
    return response.json()
```

## Use Cases

- **Document Processing**: Extract text from scanned documents
- **Content Moderation**: Detect inappropriate content
- **Product Cataloging**: Classify and tag product images
- **Quality Control**: Assess image quality for uploads
- **Security**: Face detection for access control
- **Analytics**: Color and composition analysis for design
- **Accessibility**: Generate image descriptions

## Tags

`image`, `analysis`, `vision`, `ai`, `utility`, `ocr`, `detection`, `classification`

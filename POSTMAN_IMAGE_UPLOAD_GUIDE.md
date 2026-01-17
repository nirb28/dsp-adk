# How to Send Images Directly from Postman

The Image Analysis Tool now supports **three ways** to provide images:

1. **File Path** - Reference a local file path on the server
2. **Base64 Data** - Send the image as base64-encoded data in JSON
3. **URL** - Reference an image URL (mock implementation)

## Method 1: Base64 Encoded Image (Recommended for Postman)

### Step-by-Step in Postman

#### Option A: Using Pre-request Script (Easiest)

1. **Create a new POST request** to `http://localhost:8100/tools/image_analysis/execute`

2. **Add Headers:**
   - `Content-Type: application/json`
   - `Accept: application/json`

3. **Go to "Pre-request Script" tab** and add:
```javascript
// Read image file and convert to base64
const fs = require('fs');
const imagePath = 'C:/path/to/your/image.jpg'; // Change this path

try {
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');
    pm.environment.set('image_base64', base64Image);
    console.log('Image loaded successfully, size:', imageBuffer.length, 'bytes');
} catch (error) {
    console.error('Error reading image:', error);
}
```

4. **In the Body tab** (raw JSON):
```json
{
  "arguments": {
    "image_data": "{{image_base64}}",
    "analysis_type": "general"
  },
  "mock": false
}
```

5. **Click Send**

#### Option B: Manual Base64 (For Small Images)

1. **Convert your image to base64** using:
   - Online tool: https://base64.guru/converter/encode/image
   - Command line: `base64 image.jpg` (Linux/Mac) or `certutil -encode image.jpg output.txt` (Windows)
   - Python: `python -c "import base64; print(base64.b64encode(open('image.jpg','rb').read()).decode())"`

2. **Create POST request** with body:
```json
{
  "arguments": {
    "image_data": "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a...",
    "analysis_type": "general"
  },
  "mock": false
}
```

### Example Request (Base64)

```bash
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "arguments": {
      "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
      "analysis_type": "general"
    },
    "mock": false
  }'
```

### PowerShell Example (Base64)

```powershell
# Read and encode image
$imagePath = "C:\path\to\image.jpg"
$imageBytes = [System.IO.File]::ReadAllBytes($imagePath)
$base64Image = [System.Convert]::ToBase64String($imageBytes)

# Create request
$body = @{
    arguments = @{
        image_data = $base64Image
        analysis_type = "general"
    }
    mock = $false
} | ConvertTo-Json -Depth 10

# Send request
Invoke-RestMethod -Uri "http://localhost:8100/tools/image_analysis/execute" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

## Method 2: File Path (Server-Side Files)

Use this when the image is already on the server:

```json
{
  "arguments": {
    "image_path": "d:/ds/work/workspace/git/dsp-adk/data/fraud_detection/sample_checks/check_001.jpg",
    "analysis_type": "general"
  },
  "mock": false
}
```

## Method 3: Data URL Format

You can also send images with the data URL prefix:

```json
{
  "arguments": {
    "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD...",
    "analysis_type": "object_detection"
  },
  "mock": false
}
```

The tool automatically strips the `data:image/jpeg;base64,` prefix.

## Complete Postman Collection Example

Here's a complete request with all options:

### Request: Analyze Image with Base64 Data

**Method:** POST  
**URL:** `http://localhost:8100/tools/image_analysis/execute`

**Headers:**
```
Content-Type: application/json
Accept: application/json
```

**Pre-request Script:**
```javascript
const fs = require('fs');
// Update this path to your image
const imagePath = pm.environment.get('image_file_path') || 'C:/temp/test.jpg';

try {
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');
    pm.environment.set('current_image_base64', base64Image);
    console.log(`✓ Image loaded: ${imagePath}`);
    console.log(`  Size: ${(imageBuffer.length / 1024).toFixed(2)} KB`);
} catch (error) {
    console.error('✗ Error reading image:', error.message);
    pm.environment.set('current_image_base64', '');
}
```

**Body (raw JSON):**
```json
{
  "arguments": {
    "image_data": "{{current_image_base64}}",
    "analysis_type": "general",
    "options": {}
  },
  "mock": false
}
```

**Tests (Optional):**
```javascript
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

pm.test("Analysis successful", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.success).to.be.true;
    pm.expect(jsonData.result.success).to.be.true;
});

pm.test("Image metadata present", function () {
    const jsonData = pm.response.json();
    pm.expect(jsonData.result.metadata).to.exist;
    console.log("Image dimensions:", 
        jsonData.result.metadata.width, "x", 
        jsonData.result.metadata.height);
});
```

## Python Example (For Testing)

```python
import requests
import base64

# Read and encode image
with open('path/to/image.jpg', 'rb') as f:
    image_data = base64.b64encode(f.read()).decode('utf-8')

# Send request
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

print(response.json())
```

## Response Format

```json
{
  "success": true,
  "tool_id": "image_analysis",
  "result": {
    "success": true,
    "analysis_type": "general",
    "image_source": "base64_data",
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

## Tips

1. **Image Size Limits**: Base64 encoding increases size by ~33%. Keep images under 5MB for best performance.

2. **Environment Variables**: Store the image path in Postman environment variables for easy switching:
   - Variable: `image_file_path`
   - Value: `C:/path/to/your/image.jpg`

3. **Multiple Images**: Create a collection with different images for testing:
   ```javascript
   // In Pre-request Script
   const images = {
       'portrait': 'C:/images/portrait.jpg',
       'landscape': 'C:/images/landscape.jpg',
       'document': 'C:/images/document.jpg'
   };
   const selectedImage = pm.environment.get('test_image_type') || 'portrait';
   const imagePath = images[selectedImage];
   ```

4. **Error Handling**: The tool validates both image_path and image_data. If neither is provided, you'll get:
   ```json
   {
     "success": false,
     "error": "Either image_path or image_data must be provided"
   }
   ```

## Comparison: Path vs Base64

| Method | Pros | Cons | Use Case |
|--------|------|------|----------|
| **File Path** | Simple, no encoding needed | Image must be on server | Server-side processing |
| **Base64 Data** | Send from anywhere, no server files needed | Larger payload size | Client uploads, Postman testing |
| **URL** | No local storage needed | Requires download (not fully implemented) | Public images |

## Next Steps

1. Import the updated Postman collection
2. Set up environment variables for image paths
3. Test with your own images
4. Integrate with your agents and workflows

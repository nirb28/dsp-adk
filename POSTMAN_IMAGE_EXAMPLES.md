# Postman Image Upload Examples - Quick Reference

## 🎯 Three Ways to Send Images

### Method 1: Base64 with Pre-request Script ⭐ RECOMMENDED

**Setup Once:**
1. Create Postman Environment Variable:
   - Name: `image_file_path`
   - Value: `C:/path/to/your/image.jpg`

2. Add Pre-request Script:
```javascript
const fs = require('fs');
const imagePath = pm.environment.get('image_file_path') || 'C:/temp/test.jpg';

try {
    const imageBuffer = fs.readFileSync(imagePath);
    const base64Image = imageBuffer.toString('base64');
    pm.environment.set('current_image_base64', base64Image);
    console.log('✓ Image loaded:', (imageBuffer.length / 1024).toFixed(2), 'KB');
} catch (error) {
    console.error('✗ Error:', error.message);
}
```

3. Request Body:
```json
{
  "arguments": {
    "image_data": "{{current_image_base64}}",
    "analysis_type": "general"
  },
  "mock": false
}
```

**Pros:** ✅ Easy to switch images, ✅ Works from any location, ✅ Reusable  
**Cons:** ⚠️ Requires Node.js in Postman

---

### Method 2: Manual Base64 (Small Images)

**For Quick Tests:**

1. Convert image to base64:
   ```bash
   # PowerShell
   [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\image.jpg"))
   
   # Python
   python -c "import base64; print(base64.b64encode(open('image.jpg','rb').read()).decode())"
   
   # Online: https://base64.guru/converter/encode/image
   ```

2. Request Body:
```json
{
  "arguments": {
    "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAY...",
    "analysis_type": "general"
  },
  "mock": false
}
```

**Pros:** ✅ Simple, ✅ No scripts needed  
**Cons:** ⚠️ Manual process, ⚠️ Large payloads for big images

---

### Method 3: File Path (Server-Side)

**When Image is on Server:**

```json
{
  "arguments": {
    "image_path": "d:/ds/work/workspace/git/dsp-adk/data/fraud_detection/sample_checks/check_001.jpg",
    "analysis_type": "general"
  },
  "mock": false
}
```

**Pros:** ✅ Simple, ✅ Small payload  
**Cons:** ⚠️ Image must exist on server

---

## 📋 Complete Postman Request Template

**URL:** `POST http://localhost:8100/tools/image_analysis/execute`

**Headers:**
```
Content-Type: application/json
Accept: application/json
```

**Pre-request Script (Optional):**
```javascript
const fs = require('fs');
const imagePath = pm.environment.get('image_file_path') || 'C:/temp/test.jpg';

try {
    const imageBuffer = fs.readFileSync(imagePath);
    pm.environment.set('current_image_base64', imageBuffer.toString('base64'));
    console.log('✓ Loaded:', imagePath);
} catch (error) {
    console.error('✗ Error:', error.message);
}
```

**Body (Choose One):**

```json
// Option A: Base64 Data
{
  "arguments": {
    "image_data": "{{current_image_base64}}",
    "analysis_type": "general"
  },
  "mock": false
}

// Option B: File Path
{
  "arguments": {
    "image_path": "/path/to/image.jpg",
    "analysis_type": "general"
  },
  "mock": false
}
```

**Tests (Optional):**
```javascript
pm.test("Status code is 200", () => pm.response.to.have.status(200));
pm.test("Analysis successful", () => {
    const data = pm.response.json();
    pm.expect(data.success).to.be.true;
    console.log("Dimensions:", data.result.metadata.width, "x", data.result.metadata.height);
});
```

---

## 🚀 Quick Start Steps

### For Postman Desktop:

1. **Import Collection:**
   - Import `postman_image_analysis_with_base64.json`

2. **Set Environment Variable:**
   - Create environment or use existing
   - Add variable: `image_file_path` = `C:/your/image.jpg`

3. **Select Request:**
   - Choose "Upload Image - Base64 with Pre-request Script"

4. **Send Request:**
   - Click Send
   - Check Console for image load confirmation

### For cURL:

```bash
# Convert image to base64 first
IMAGE_BASE64=$(python -c "import base64; print(base64.b64encode(open('image.jpg','rb').read()).decode())")

# Send request
curl -X POST "http://localhost:8100/tools/image_analysis/execute" \
  -H "Content-Type: application/json" \
  -d "{
    \"arguments\": {
      \"image_data\": \"$IMAGE_BASE64\",
      \"analysis_type\": \"general\"
    },
    \"mock\": false
  }"
```

---

## 📊 Comparison Table

| Feature | Base64 (Script) | Base64 (Manual) | File Path |
|---------|----------------|-----------------|-----------|
| **Ease of Use** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Flexibility** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **Payload Size** | Large | Large | Small |
| **Setup Time** | One-time | Per image | None |
| **Best For** | Testing multiple images | Quick tests | Server files |

---

## 💡 Tips & Tricks

### 1. Multiple Test Images
```javascript
// Pre-request Script
const images = {
    'portrait': 'C:/images/portrait.jpg',
    'landscape': 'C:/images/landscape.jpg',
    'document': 'C:/images/document.jpg'
};

const imageType = pm.environment.get('test_image_type') || 'portrait';
const imagePath = images[imageType];
const imageBuffer = fs.readFileSync(imagePath);
pm.environment.set('current_image_base64', imageBuffer.toString('base64'));
```

### 2. Image Size Check
```javascript
// Pre-request Script
const imageBuffer = fs.readFileSync(imagePath);
const sizeKB = imageBuffer.length / 1024;

if (sizeKB > 5000) {
    console.warn('⚠️ Image is large:', sizeKB.toFixed(2), 'KB');
    console.warn('   Consider resizing for better performance');
}
```

### 3. Automatic Format Detection
```javascript
// Tests
pm.test("Image format detected", () => {
    const data = pm.response.json();
    const format = data.result.metadata.format;
    console.log("Detected format:", format);
    pm.expect(['JPEG', 'PNG', 'GIF', 'BMP']).to.include(format);
});
```

---

## 🔧 Troubleshooting

### Error: "Either image_path or image_data must be provided"
- ✅ Make sure you're sending at least one parameter
- ✅ Check that `{{current_image_base64}}` is not empty

### Error: "Failed to decode base64 image data"
- ✅ Verify base64 string is valid
- ✅ Check for extra whitespace or newlines
- ✅ Ensure image file was read correctly

### Pre-request Script Not Running
- ✅ Check Postman Console for errors
- ✅ Verify file path is correct
- ✅ Ensure Postman has file system access

### Image Too Large
- ✅ Resize image before encoding
- ✅ Use JPEG with lower quality
- ✅ Consider using file path method instead

---

## 📚 Related Files

- **Full Documentation:** `IMAGE_ANALYSIS_TOOL.md`
- **Upload Guide:** `POSTMAN_IMAGE_UPLOAD_GUIDE.md`
- **Quick Start:** `IMAGE_ANALYSIS_QUICKSTART.md`
- **Collection (Basic):** `postman_image_analysis.json`
- **Collection (Base64):** `postman_image_analysis_with_base64.json`

---

## ✅ Verification

Test your setup with this tiny 1x1 pixel image:

```json
{
  "arguments": {
    "image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
    "analysis_type": "general"
  },
  "mock": false
}
```

Expected response:
```json
{
  "success": true,
  "result": {
    "image_source": "base64_data",
    "metadata": {
      "width": 1,
      "height": 1,
      "format": "PNG"
    }
  }
}
```

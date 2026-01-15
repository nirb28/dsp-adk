# Sample Images Guide for Fraud Detection Testing

## Overview

This guide provides sources and instructions for obtaining sample check images and signatures for testing the fraud detection system.

## ⚠️ Important Security Notice

**NEVER use real checks or signatures for testing!**
- Use only synthetic, mock, or public domain images
- Never commit real financial documents to version control
- Follow PCI-DSS and data privacy regulations

## Directory Structure

Create the following directories for sample data:

```bash
data/
├── fraud_detection/
│   ├── sample_checks/          # Check images for analysis
│   ├── sample_signatures/      # Known valid signature samples
│   └── test_results/           # Analysis output (optional)
```

## Quick Setup

```powershell
# Create directories
New-Item -ItemType Directory -Force -Path "data\fraud_detection\sample_checks"
New-Item -ItemType Directory -Force -Path "data\fraud_detection\sample_signatures"
New-Item -ItemType Directory -Force -Path "data\fraud_detection\test_results"
```

## Sample Image Sources

### Option 1: Public Domain Check Templates (Recommended)

#### Blank Check Templates
These are legal, publicly available blank check templates:

1. **Template.net** - Free blank check templates
   - URL: https://www.template.net/business/check-templates/blank-check-template/
   - Format: PDF, JPG
   - License: Free for personal/educational use

2. **Vertex42** - Printable blank checks
   - URL: https://www.vertex42.com/ExcelTemplates/printable-checks.html
   - Format: Excel, PDF
   - License: Free for personal use

3. **PDFfiller** - Blank check samples
   - URL: https://www.pdffiller.com/en/catalog/blank-check.htm
   - Format: PDF
   - License: Free samples available

#### How to Use Templates:
```powershell
# Download template PDF
# Convert to JPG using online converter or:
# Install ImageMagick: winget install ImageMagick.ImageMagick
# Convert PDF to JPG:
magick convert -density 300 blank_check.pdf -quality 90 data/fraud_detection/sample_checks/check_001.jpg
```

### Option 2: Generate Synthetic Checks with AI

Use AI image generation tools to create synthetic check images:

#### DALL-E / Midjourney / Stable Diffusion
Prompt examples:
```
"A blank personal check template with standard check elements, 
watermark visible, professional banking design, high quality scan, 
300 DPI, no personal information"

"Bank check template showing signature line, amount field, 
date field, payee line, bank watermark, microprinting visible"
```

#### Canva
1. Go to https://www.canva.com
2. Search for "check template"
3. Customize and download as JPG (300 DPI)

### Option 3: Create Mock Checks Programmatically

Use Python to generate synthetic check images:

```python
from PIL import Image, ImageDraw, ImageFont
import random

def create_mock_check(output_path, check_number=1001):
    """Create a synthetic check image for testing."""
    # Create blank check (standard US check size: 6" x 2.75" at 300 DPI)
    width, height = 1800, 825
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Add border
    draw.rectangle([(10, 10), (width-10, height-10)], outline='black', width=3)
    
    # Add check elements
    # Date field
    draw.text((1400, 50), "Date: ___________", fill='black')
    
    # Pay to the order of
    draw.text((50, 200), "Pay to the order of: _________________________", fill='black')
    
    # Amount box
    draw.rectangle([(1400, 180), (1750, 230)], outline='black', width=2)
    draw.text((1410, 195), "$________", fill='black')
    
    # Amount in words
    draw.text((50, 300), "_________________________________________ Dollars", fill='black')
    
    # Bank info
    draw.text((50, 450), "SAMPLE BANK", fill='blue')
    draw.text((50, 500), "123 Main Street, City, ST 12345", fill='blue')
    
    # Memo line
    draw.text((50, 650), "Memo: ___________", fill='black')
    
    # Signature line
    draw.text((900, 650), "Signature: ___________________", fill='black')
    
    # Check number
    draw.text((1600, 750), f"Check #{check_number}", fill='black')
    
    # Routing numbers (fake)
    draw.text((50, 750), "|:012345678|: 9876543210|| 1001", fill='black')
    
    # Add watermark text
    watermark_font = ImageFont.truetype("arial.ttf", 60) if hasattr(ImageFont, 'truetype') else None
    draw.text((width//2 - 200, height//2 - 50), "SAMPLE", fill=(200, 200, 200), font=watermark_font)
    
    # Save
    img.save(output_path, 'JPEG', quality=95, dpi=(300, 300))
    print(f"Created mock check: {output_path}")

# Generate sample checks
for i in range(1, 4):
    create_mock_check(f"data/fraud_detection/sample_checks/check_{i:03d}.jpg", 1000 + i)
```

### Option 4: Signature Samples

#### Create Synthetic Signatures

```python
from PIL import Image, ImageDraw
import random

def create_mock_signature(output_path, variation=0):
    """Create a synthetic signature image."""
    width, height = 600, 200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create a simple signature-like curve
    points = []
    x = 50
    for i in range(20):
        y = 100 + random.randint(-30, 30) + (variation * 5)
        points.append((x, y))
        x += 25
    
    # Draw signature
    draw.line(points, fill='blue', width=3)
    
    # Add some flourish
    draw.arc([(400, 80), (550, 120)], 0, 180, fill='blue', width=2)
    
    img.save(output_path, 'JPEG', quality=95, dpi=(150, 150))
    print(f"Created mock signature: {output_path}")

# Generate signature samples
for i in range(1, 6):
    create_mock_signature(f"data/fraud_detection/sample_signatures/sig_{i:03d}.jpg", variation=i)
```

## Downloading Pre-made Test Images

### GitHub Repositories with Sample Data

1. **Check Image Dataset** (if available publicly)
   ```bash
   # Example - check for public datasets
   # Search GitHub for "check image dataset" or "bank check samples"
   ```

2. **Document Analysis Datasets**
   - MNIST Bank Check Dataset (if publicly available)
   - Document Image Analysis datasets from academic sources

### Academic Datasets

1. **ICDAR (International Conference on Document Analysis)**
   - URL: https://www.icdar2021.org/
   - May have document analysis datasets

2. **Kaggle Datasets**
   - Search: https://www.kaggle.com/datasets
   - Keywords: "check", "signature", "document verification"

## Quick Test Setup Script

Save this as `setup_test_data.py` in the project root:

```python
"""
Quick setup script to generate test data for fraud detection.
Run this to create sample checks and signatures for testing.
"""

import os
from PIL import Image, ImageDraw, ImageFont
import random

def setup_directories():
    """Create necessary directories."""
    dirs = [
        "data/fraud_detection/sample_checks",
        "data/fraud_detection/sample_signatures",
        "data/fraud_detection/test_results"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"✓ Created directory: {d}")

def create_mock_check(output_path, check_number=1001, has_issues=False):
    """Create a synthetic check image."""
    width, height = 1800, 825
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Border
    draw.rectangle([(10, 10), (width-10, height-10)], outline='black', width=3)
    
    # Check elements
    draw.text((1400, 50), "Date: 01/13/2026", fill='black')
    draw.text((50, 200), "Pay to the order of: John Doe", fill='black')
    draw.rectangle([(1400, 180), (1750, 230)], outline='black', width=2)
    draw.text((1410, 195), "$1,000.00", fill='black')
    draw.text((50, 300), "One Thousand and 00/100 Dollars", fill='black')
    draw.text((50, 450), "SAMPLE BANK", fill='blue')
    draw.text((50, 500), "123 Main Street, City, ST 12345", fill='blue')
    draw.text((50, 650), "Memo: Test Payment", fill='black')
    draw.text((900, 650), "Signature: ___________________", fill='black')
    draw.text((1600, 750), f"Check #{check_number}", fill='black')
    draw.text((50, 750), "|:012345678|: 9876543210|| " + str(check_number), fill='black')
    
    # Watermark
    draw.text((width//2 - 200, height//2 - 50), "SAMPLE", fill=(220, 220, 220))
    
    # Add issues if requested
    if has_issues:
        # Simulate tampering - different color for amount
        draw.text((1410, 195), "$5,000.00", fill='red')
    
    img.save(output_path, 'JPEG', quality=95, dpi=(300, 300))
    return output_path

def create_mock_signature(output_path, variation=0):
    """Create a synthetic signature."""
    width, height = 600, 200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Signature curve
    points = [(50 + i*25, 100 + random.randint(-30, 30) + variation*5) for i in range(20)]
    draw.line(points, fill='blue', width=3)
    draw.arc([(400, 80), (550, 120)], 0, 180, fill='blue', width=2)
    
    img.save(output_path, 'JPEG', quality=95, dpi=(150, 150))
    return output_path

def main():
    """Generate all test data."""
    print("Setting up fraud detection test data...")
    print("=" * 60)
    
    # Create directories
    setup_directories()
    print()
    
    # Generate checks
    print("Generating sample checks...")
    checks = []
    for i in range(1, 4):
        path = f"data/fraud_detection/sample_checks/check_{i:03d}.jpg"
        create_mock_check(path, 1000 + i, has_issues=(i == 3))
        checks.append(path)
        print(f"✓ Created: {path}")
    print()
    
    # Generate signatures
    print("Generating sample signatures...")
    signatures = []
    for i in range(1, 6):
        path = f"data/fraud_detection/sample_signatures/sig_{i:03d}.jpg"
        create_mock_signature(path, variation=i)
        signatures.append(path)
        print(f"✓ Created: {path}")
    print()
    
    print("=" * 60)
    print("✓ Test data setup complete!")
    print()
    print("Sample checks created:")
    for c in checks:
        print(f"  - {c}")
    print()
    print("Sample signatures created:")
    for s in signatures:
        print(f"  - {s}")
    print()
    print("You can now run the fraud detection example:")
    print("  python examples/fraud_detection/fraud_detection_example.py")

if __name__ == "__main__":
    main()
```

## Running the Setup

```powershell
# Run the setup script
python setup_test_data.py

# Verify files were created
Get-ChildItem -Path "data\fraud_detection\sample_checks"
Get-ChildItem -Path "data\fraud_detection\sample_signatures"
```

## Image Requirements

### Check Images
- **Format**: JPG, PNG
- **Resolution**: 300 DPI minimum
- **Size**: 1800x825 pixels (standard US check at 300 DPI)
- **Color**: RGB
- **Quality**: High quality, no blur
- **Content**: Should include:
  - Date field
  - Payee line
  - Amount box and written amount
  - Signature line
  - Bank information
  - Check number
  - Routing/account numbers
  - Watermark (optional but recommended)

### Signature Images
- **Format**: JPG, PNG
- **Resolution**: 150 DPI minimum
- **Size**: 600x200 pixels recommended
- **Color**: RGB or grayscale
- **Background**: White or light background
- **Quality**: Clear, high contrast
- **Quantity**: 3-5 samples for best comparison results

## Testing the Setup

After creating sample images, test with:

```powershell
# Run the test suite (uses mock data, no images needed)
python test_fraud_detection.py

# Run with actual images
python examples/fraud_detection/fraud_detection_example.py
```

## Example File Paths

Update the example script with your file paths:

```python
# In fraud_detection_example.py
CHECK_IMAGE = "data/fraud_detection/sample_checks/check_001.jpg"
SIGNATURE_SAMPLES = [
    "data/fraud_detection/sample_signatures/sig_001.jpg",
    "data/fraud_detection/sample_signatures/sig_002.jpg",
    "data/fraud_detection/sample_signatures/sig_003.jpg"
]
EXPECTED_WATERMARK = "SAMPLE watermark"
```

## Legal and Ethical Considerations

1. **Never use real checks**: Always use synthetic or template data
2. **Respect privacy**: Don't use images containing real personal information
3. **Follow regulations**: Comply with PCI-DSS and data protection laws
4. **Educational use only**: These samples are for testing and development
5. **Secure disposal**: Delete test images when no longer needed

## Troubleshooting

### Issue: Images not loading
```python
from PIL import Image
img = Image.open("path/to/check.jpg")
print(f"Size: {img.size}, Format: {img.format}, Mode: {img.mode}")
```

### Issue: Low quality images
- Ensure DPI is at least 300 for checks, 150 for signatures
- Use JPEG quality 90+ when saving
- Avoid compression artifacts

### Issue: API errors with images
- Check file size (should be < 5MB)
- Verify image format is supported (JPG, PNG)
- Ensure images are properly encoded

## Next Steps

1. Run `setup_test_data.py` to generate sample images
2. Verify images were created correctly
3. Update example script with correct paths
4. Run fraud detection example
5. Review results and adjust as needed

## Resources

- **PIL/Pillow Documentation**: https://pillow.readthedocs.io/
- **Check Template Standards**: US check dimensions and formats
- **Image Processing**: OpenCV, ImageMagick for advanced manipulation
- **Dataset Sources**: Kaggle, academic repositories, public domain sources

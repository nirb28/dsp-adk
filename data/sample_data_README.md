# Sample Data Structure for Fraud Detection

## Directory Structure

To use the fraud detection system, organize your sample data as follows:

```
data/
├── sample_checks/          # Check images to analyze
│   ├── check_001.jpg
│   ├── check_002.jpg
│   └── check_003.jpg
│
├── sample_signatures/      # Known valid signature samples
│   ├── sig_001.jpg
│   ├── sig_002.jpg
│   └── sig_003.jpg
│
└── sample_data_README.md   # This file
```

## Image Requirements

### Check Images
- **Format**: JPG, PNG, or TIFF
- **Resolution**: Minimum 300 DPI recommended
- **Size**: 1-5 MB per image
- **Quality**: Clear, well-lit, no blur
- **Orientation**: Horizontal (landscape)

### Signature Samples
- **Format**: JPG or PNG
- **Resolution**: Minimum 150 DPI
- **Size**: 100 KB - 1 MB per image
- **Quality**: High contrast, clear signature
- **Background**: White or light background preferred
- **Quantity**: 3-5 samples recommended for best results

## Sample Data Sources

### For Testing
1. **Create mock checks**: Use image editing software to create sample checks
2. **Use public domain images**: Search for "sample check" or "blank check template"
3. **Generate synthetic data**: Use AI image generation for test data

### For Production
1. **Scan actual checks**: Use high-quality scanner (300+ DPI)
2. **Mobile capture**: Use mobile app with document scanning
3. **Digital checks**: Export from banking software

## Privacy and Security

⚠️ **IMPORTANT**: Never commit real check images or signatures to version control!

- Add `data/sample_checks/` to `.gitignore`
- Add `data/sample_signatures/` to `.gitignore`
- Use anonymized or synthetic data for testing
- Encrypt sensitive data at rest
- Follow PCI-DSS compliance for production use

## Example Usage

```python
# Example paths for fraud detection
CHECK_IMAGE = "data/sample_checks/check_001.jpg"
SIGNATURE_SAMPLES = [
    "data/sample_signatures/sig_001.jpg",
    "data/sample_signatures/sig_002.jpg",
    "data/sample_signatures/sig_003.jpg"
]
```

## Creating Test Data

### Option 1: Download Sample Images
```bash
# Create directories
mkdir -p data/sample_checks
mkdir -p data/sample_signatures

# Download sample check templates (use legal, public domain sources)
# Example: https://www.templateroller.com/template/blank-check-template.html
```

### Option 2: Generate Synthetic Data
Use AI image generation tools to create synthetic check images for testing.

### Option 3: Use Provided Mock Data
The test script (`test_fraud_detection.py`) uses mock responses and doesn't require actual images.

## Watermark Descriptions

When analyzing checks, provide accurate watermark descriptions:

### Common Bank Watermarks
- **Bank of America**: "Bank of America" text with eagle emblem
- **Chase**: "JPMorgan Chase" with octagonal logo
- **Wells Fargo**: "Wells Fargo" with stagecoach watermark
- **Citibank**: "Citibank" text with umbrella logo

### Generic Check Features
- Microprinting along borders
- Color-shifting ink on amount field
- Security thread embedded in paper
- UV-reactive elements
- Thermochromic ink

## Focus Areas for Tampering Detection

Specify these areas when analyzing checks:

1. **amount** - Dollar amount field (critical)
2. **payee** - "Pay to the order of" field (critical)
3. **date** - Date field
4. **signature** - Signature line
5. **memo** - Memo/note field
6. **account_number** - Bank account number
7. **routing_number** - Bank routing number

## Troubleshooting

### Poor Results
- **Issue**: Low fraud detection accuracy
- **Solution**: Use higher resolution images, provide more signature samples

### API Errors
- **Issue**: Vision API timeouts
- **Solution**: Reduce image file size, compress images before upload

### Missing Features
- **Issue**: Watermark not detected
- **Solution**: Ensure high-quality scan, adjust lighting/contrast

## Next Steps

1. Create the directory structure
2. Add sample images (or use mock testing)
3. Update `.gitignore` to exclude sensitive data
4. Run the example: `python examples/fraud_detection_example.py`
5. Review logs and results
6. Tune thresholds based on your requirements

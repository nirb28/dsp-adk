# Fraud Detection System - Quick Setup Guide

## 📁 New Folder Structure

All fraud detection files are now organized in dedicated subfolders:

```
dsp-adk/
├── tools/fraud_detection/              # Tool implementation
├── data/fraud_detection/               # Configs & sample data
│   ├── agents/                         # Agent configurations
│   ├── graphs/                         # LangGraph workflows
│   ├── tools/                          # Tool configurations
│   ├── sample_checks/                  # Check images (gitignored)
│   ├── sample_signatures/              # Signatures (gitignored)
│   └── test_results/                   # Results (gitignored)
├── examples/fraud_detection/           # Example scripts
├── docs/fraud_detection/               # Documentation
├── setup_test_data.py                  # Generate test images
└── test_fraud_detection.py             # Test suite
```

## 🚀 Quick Start (3 Steps)

### Step 1: Generate Test Images

```bash
python setup_test_data.py
```

This creates:
- ✅ 3 sample check images (including 1 with fraud indicators)
- ✅ 5 signature samples with natural variations
- ✅ All images saved to `data/fraud_detection/sample_checks/` and `sample_signatures/`

### Step 2: Run Tests

```bash
python test_fraud_detection.py
```

Expected output:
```
ALL TESTS PASSED ✓
```

### Step 3: Run Full Example

```bash
# Set your API credentials
$env:OPENAI_API_KEY="your-api-key-here"
$env:OPENAI_API_ENDPOINT="https://api.openai.com/v1/chat/completions"

# Run the fraud detection example
python examples/fraud_detection/fraud_detection_example.py
```

## 📥 Sample Images - Multiple Options

### Option 1: Auto-Generate (Recommended) ⭐

```bash
python setup_test_data.py
```

**Creates**:
- Synthetic check images with all required fields
- Signature samples with natural variations
- One check with intentional fraud indicators for testing

### Option 2: Download Public Domain Templates

**Sources**:
1. **Template.net** - https://www.template.net/business/check-templates/blank-check-template/
2. **Vertex42** - https://www.vertex42.com/ExcelTemplates/printable-checks.html
3. **PDFfiller** - https://www.pdffiller.com/en/catalog/blank-check.htm

**Convert PDF to JPG**:
```bash
# Using ImageMagick
magick convert -density 300 blank_check.pdf data/fraud_detection/sample_checks/check_001.jpg
```

### Option 3: AI-Generated Images

**DALL-E / Midjourney / Stable Diffusion Prompts**:
```
"A blank personal check template with standard check elements, 
watermark visible, professional banking design, high quality scan, 
300 DPI, no personal information"
```

**Canva**:
1. Go to https://www.canva.com
2. Search "check template"
3. Customize and download as JPG (300 DPI)

### Option 4: Programmatic Generation

See detailed Python scripts in:
- `data/fraud_detection/SAMPLE_IMAGES_GUIDE.md`
- `setup_test_data.py` (source code)

## 📚 Documentation

All documentation is in `docs/fraud_detection/`:

| Document | Purpose |
|----------|---------|
| **INDEX.md** | Documentation index and quick links |
| **FRAUD_DETECTION_QUICKSTART.md** | Quick start guide |
| **FRAUD_DETECTION_README.md** | Complete system documentation |
| **IMPLEMENTATION_SUMMARY.md** | Technical implementation details |
| **REORGANIZATION_SUMMARY.md** | File structure changes |

Module-specific docs in `data/fraud_detection/`:

| Document | Purpose |
|----------|---------|
| **README.md** | Module overview |
| **SAMPLE_IMAGES_GUIDE.md** | Comprehensive image acquisition guide |

## 🔧 Import Paths (Updated)

```python
# Tool
from tools.fraud_detection.image_fraud_detector import ImageFraudDetector

# Example
from examples.fraud_detection.fraud_detection_example import FraudDetectionVotingSystem
```

## 📂 File Paths (Updated)

```python
# Check images
CHECK_IMAGE = "data/fraud_detection/sample_checks/check_001.jpg"

# Signature samples
SIGNATURE_SAMPLES = [
    "data/fraud_detection/sample_signatures/sig_001.jpg",
    "data/fraud_detection/sample_signatures/sig_002.jpg",
    "data/fraud_detection/sample_signatures/sig_003.jpg"
]
```

## 🔒 Security

**Protected by .gitignore**:
- `data/fraud_detection/sample_checks/*` (except .gitkeep)
- `data/fraud_detection/sample_signatures/*` (except .gitkeep)
- `data/fraud_detection/test_results/*` (except .gitkeep)
- `fraud_analysis_*.json`
- `fraud_detection.log`

**⚠️ NEVER commit real checks or signatures!**

## ✅ Verification Checklist

- [ ] Run `python setup_test_data.py` - Creates test images
- [ ] Run `python test_fraud_detection.py` - All tests pass
- [ ] Check `data/fraud_detection/sample_checks/` - Contains 3 images
- [ ] Check `data/fraud_detection/sample_signatures/` - Contains 5 images
- [ ] Set environment variables (OPENAI_API_KEY, OPENAI_API_ENDPOINT)
- [ ] Run `python examples/fraud_detection/fraud_detection_example.py`
- [ ] Review results in console and JSON output

## 🎯 What's Included

### Components
- ✅ Image fraud detector tool with 4 analysis modes
- ✅ 3 specialized agents (signature, watermark, tampering)
- ✅ LangGraph multi-agent voting workflow
- ✅ Comprehensive example with detailed logging
- ✅ Complete test suite
- ✅ Test data generator

### Documentation
- ✅ Quick start guide
- ✅ Complete system documentation
- ✅ Implementation details
- ✅ Sample images guide
- ✅ Reorganization summary
- ✅ Documentation index

### Sample Data
- ✅ Auto-generated check images
- ✅ Auto-generated signature samples
- ✅ Intentional fraud examples for testing

## 🆘 Troubleshooting

### Issue: No sample images
```bash
python setup_test_data.py
```

### Issue: Import errors
Check import paths - they've been updated to `tools.fraud_detection.*`

### Issue: API authentication
```bash
$env:OPENAI_API_KEY="your-key"
$env:OPENAI_API_ENDPOINT="https://api.openai.com/v1/chat/completions"
```

### Issue: Tests failing
Ensure you're in the project root directory when running tests

## 📖 Next Steps

1. **New to fraud detection?** → Read `docs/fraud_detection/FRAUD_DETECTION_QUICKSTART.md`
2. **Need test images?** → Run `python setup_test_data.py`
3. **Want to customize?** → See `docs/fraud_detection/FRAUD_DETECTION_README.md`
4. **Ready to integrate?** → Review `docs/fraud_detection/IMPLEMENTATION_SUMMARY.md`

## 📞 Support

- **Documentation**: `docs/fraud_detection/INDEX.md`
- **Module README**: `data/fraud_detection/README.md`
- **Sample Images**: `data/fraud_detection/SAMPLE_IMAGES_GUIDE.md`

---

**Ready to start?** Run `python setup_test_data.py` to generate test images!

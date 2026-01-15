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
    
    # Add inner decorative border
    draw.rectangle([(20, 20), (width-20, height-20)], outline='gray', width=1)
    
    # Check elements
    draw.text((1400, 50), "Date: 01/13/2026", fill='black')
    draw.text((50, 200), "Pay to the order of: John Doe", fill='black')
    
    # Amount box
    draw.rectangle([(1400, 180), (1750, 230)], outline='black', width=2)
    amount_text = "$5,000.00" if has_issues else "$1,000.00"
    amount_color = 'red' if has_issues else 'black'
    draw.text((1410, 195), amount_text, fill=amount_color)
    
    # Amount in words
    amount_words = "Five Thousand and 00/100" if has_issues else "One Thousand and 00/100"
    draw.text((50, 300), f"{amount_words} Dollars", fill='black')
    
    # Bank info
    draw.text((50, 450), "SAMPLE BANK", fill='blue')
    draw.text((50, 480), "123 Main Street", fill='blue')
    draw.text((50, 510), "City, ST 12345", fill='blue')
    
    # Memo line
    draw.text((50, 650), "Memo: Test Payment", fill='black')
    
    # Signature line
    draw.text((900, 650), "Signature: ___________________", fill='black')
    
    # Check number
    draw.text((1600, 750), f"Check #{check_number}", fill='black')
    
    # Routing numbers (fake MICR line)
    draw.text((50, 750), f"|:012345678|: 9876543210|| {check_number}", fill='black')
    
    # Add watermark text (light gray)
    try:
        watermark_font = ImageFont.truetype("arial.ttf", 80)
    except:
        watermark_font = ImageFont.load_default()
    
    # Rotate watermark
    watermark_img = Image.new('RGBA', (width, height), (255, 255, 255, 0))
    watermark_draw = ImageDraw.Draw(watermark_img)
    watermark_draw.text((width//2 - 200, height//2 - 50), "SAMPLE", fill=(220, 220, 220, 128), font=watermark_font)
    
    # Composite watermark
    img.paste(watermark_img, (0, 0), watermark_img)
    
    # Add security features text
    draw.text((1400, 700), "VOID IF ALTERED", fill=(200, 200, 200))
    
    img.save(output_path, 'JPEG', quality=95, dpi=(300, 300))
    return output_path

def create_mock_signature(output_path, variation=0):
    """Create a synthetic signature."""
    width, height = 600, 200
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create signature curve with variation
    points = []
    x = 50
    base_y = 100
    
    for i in range(20):
        # Add natural variation
        y_offset = random.randint(-30, 30)
        # Add systematic variation for different signatures
        y_variation = variation * 5
        y = base_y + y_offset + y_variation
        points.append((x, y))
        x += 25
    
    # Draw signature line
    draw.line(points, fill='blue', width=3)
    
    # Add flourish at the end
    flourish_start = (400, 80 + variation * 3)
    flourish_end = (550, 120 + variation * 3)
    draw.arc([flourish_start, flourish_end], 0, 180, fill='blue', width=2)
    
    # Add some dots (like initials)
    draw.ellipse([(100, 90), (110, 100)], fill='blue')
    draw.ellipse([(200, 95), (210, 105)], fill='blue')
    
    img.save(output_path, 'JPEG', quality=95, dpi=(150, 150))
    return output_path

def main():
    """Generate all test data."""
    print("=" * 70)
    print("FRAUD DETECTION TEST DATA SETUP")
    print("=" * 70)
    print()
    print("This script will create synthetic check and signature images")
    print("for testing the fraud detection system.")
    print()
    
    # Create directories
    print("Setting up directories...")
    setup_directories()
    print()
    
    # Generate checks
    print("Generating sample checks...")
    print("-" * 70)
    checks = []
    
    # Normal checks
    for i in range(1, 3):
        path = f"data/fraud_detection/sample_checks/check_{i:03d}.jpg"
        create_mock_check(path, 1000 + i, has_issues=False)
        checks.append(path)
        print(f"✓ Created normal check: {path}")
    
    # Suspicious check (altered amount)
    path = "data/fraud_detection/sample_checks/check_003.jpg"
    create_mock_check(path, 1003, has_issues=True)
    checks.append(path)
    print(f"✓ Created suspicious check (altered amount): {path}")
    print()
    
    # Generate signatures
    print("Generating sample signatures...")
    print("-" * 70)
    signatures = []
    for i in range(1, 6):
        path = f"data/fraud_detection/sample_signatures/sig_{i:03d}.jpg"
        create_mock_signature(path, variation=i)
        signatures.append(path)
        print(f"✓ Created signature sample {i}: {path}")
    print()
    
    # Summary
    print("=" * 70)
    print("✓ TEST DATA SETUP COMPLETE!")
    print("=" * 70)
    print()
    print(f"Created {len(checks)} check images:")
    for c in checks:
        print(f"  • {c}")
    print()
    print(f"Created {len(signatures)} signature samples:")
    for s in signatures:
        print(f"  • {s}")
    print()
    print("Next steps:")
    print("  1. Review the generated images in data/fraud_detection/")
    print("  2. Run the test suite: python test_fraud_detection.py")
    print("  3. Run the example: python examples/fraud_detection/fraud_detection_example.py")
    print()
    print("Note: Check #003 has been intentionally altered for testing fraud detection.")
    print("=" * 70)

if __name__ == "__main__":
    main()

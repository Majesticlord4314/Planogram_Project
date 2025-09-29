#!/usr/bin/env python3
"""
Test script for the enhanced image filtering logic
"""
import re

# Enhanced case detection patterns (handle underscores and spaces)
CASE_PATTERNS = [
    re.compile(r'iphone[_\s]*.*[_\s]*case', re.I),
    re.compile(r'case[_\s]*.*[_\s]*iphone', re.I), 
    re.compile(r'silicone[_\s]*.*[_\s]*case', re.I),
    re.compile(r'clear[_\s]*.*[_\s]*case', re.I),
    re.compile(r'magsafe[_\s]*.*[_\s]*case', re.I),
    re.compile(r'armou?r[_\s]*.*[_\s]*case', re.I),
    re.compile(r'crystal[_\s]*.*[_\s]*case', re.I),
    re.compile(r'protective[_\s]*.*[_\s]*case', re.I),
    re.compile(r'tough[_\s]*.*[_\s]*case', re.I),
    re.compile(r'rugged[_\s]*.*[_\s]*case', re.I),
    re.compile(r'shock[_\s]*.*[_\s]*case', re.I),
    re.compile(r'cover[_\s]*.*[_\s]*iphone', re.I),
    re.compile(r'iphone[_\s]*.*[_\s]*cover', re.I),
    re.compile(r'leather[_\s]*.*[_\s]*case', re.I),
]

# Enhanced screen protector detection patterns (handle underscores and spaces)
SCREEN_PATTERNS = [
    re.compile(r'screen[_\s]*.*[_\s]*protector', re.I),
    re.compile(r'tempered[_\s]*.*[_\s]*glass', re.I),
    re.compile(r'privacy[_\s]*.*[_\s]*glass', re.I),
    re.compile(r'lens[_\s]*.*[_\s]*protector', re.I),
    re.compile(r'glass[_\s]*.*[_\s]*protector', re.I),
    re.compile(r'protector[_\s]*.*[_\s]*screen', re.I),
    re.compile(r'anti[_\s]*.*[_\s]*glare', re.I),
    re.compile(r'blue[_\s]*.*[_\s]*light[_\s]*.*[_\s]*filter', re.I),
]

# Exclusion patterns for non-cases products (handle underscores and spaces)
EXCLUSION_PATTERNS = [
    re.compile(r'speaker', re.I),
    re.compile(r'headphone', re.I),
    re.compile(r'earphone', re.I),
    re.compile(r'earbuds', re.I),
    re.compile(r'airpods', re.I),
    re.compile(r'cable', re.I),
    re.compile(r'adapter', re.I),
    re.compile(r'hub', re.I),
    re.compile(r'watch[_\s]*.*[_\s]*strap', re.I),
    re.compile(r'strap', re.I),
    re.compile(r'band', re.I),
    re.compile(r'bag', re.I),
    re.compile(r'sleeve', re.I),
    re.compile(r'airtag', re.I),
    re.compile(r'charger', re.I),
    re.compile(r'powerbank', re.I),
    re.compile(r'power[_\s]*.*[_\s]*bank', re.I),
    re.compile(r'mouse', re.I),
    re.compile(r'keyboard', re.I),
    re.compile(r'stand', re.I),
    re.compile(r'mount', re.I),
    re.compile(r'holder', re.I),
    re.compile(r'wallet', re.I),
    re.compile(r'pouch', re.I),
]

def test_filtering_logic():
    # Test cases
    test_files = [
        "iphone_15_silicone_case_blue.jpg",
        "apple_iphone_14_clear_case.jpg",
        "magsafe_case_iphone_13.jpg",
        "tempered_glass_screen_protector_iphone_15.jpg",
        "privacy_glass_iphone_14.jpg",
        "bluetooth_speaker_wireless.jpg",
        "airpods_pro_case.jpg",
        "lightning_cable_usb.jpg",
        "watch_strap_leather.jpg",
        "powerbank_10000mah.jpg",
        "iphone_15_pro_max_case_leather.jpg",
        "screen_protector_anti_glare_iphone.jpg",
        "headphones_wireless_bluetooth.jpg",
        "phone_stand_adjustable.jpg",
    ]
    
    print("Testing Enhanced Image Filtering Logic")
    print("=" * 50)
    
    valid_count = 0
    excluded_count = 0
    
    for filename in test_files:
        name = filename.lower()
        
        # Check exclusion patterns first
        is_excluded = any(pattern.search(name) for pattern in EXCLUSION_PATTERNS)
        if is_excluded:
            excluded_count += 1
            print(f"❌ EXCLUDED: {filename}")
            continue
        
        # Enhanced case detection with confidence scoring
        case_matches = sum(1 for pattern in CASE_PATTERNS if pattern.search(name))
        is_case = case_matches > 0
        case_confidence = min(1.0, case_matches / 3.0)  # Normalize to 0-1 scale
        
        # Enhanced screen protector detection with confidence scoring
        screen_matches = sum(1 for pattern in SCREEN_PATTERNS if pattern.search(name))
        is_screen = screen_matches > 0
        screen_confidence = min(1.0, screen_matches / 2.0)  # Normalize to 0-1 scale
        
        # Overall confidence score (higher of case or screen confidence)
        confidence_score = max(case_confidence, screen_confidence)
        
        # Validation flag for cases wall - must be case or screen with reasonable confidence
        is_valid_for_cases_wall = (is_case or is_screen) and confidence_score >= 0.3
        
        # Determine product category
        if is_case and case_confidence >= screen_confidence:
            product_category = 'iphone_case'
        elif is_screen:
            product_category = 'screen_protector'
        else:
            product_category = 'other'
        
        if is_valid_for_cases_wall:
            valid_count += 1
            print(f"✅ VALID: {filename}")
            print(f"   Category: {product_category}, Confidence: {confidence_score:.2f}")
        else:
            print(f"⚠️  INVALID: {filename}")
            print(f"   Category: {product_category}, Confidence: {confidence_score:.2f}")
        print()
    
    print("=" * 50)
    print(f"Summary:")
    print(f"Total files tested: {len(test_files)}")
    print(f"Valid for cases wall: {valid_count}")
    print(f"Excluded products: {excluded_count}")
    print(f"Invalid/low confidence: {len(test_files) - valid_count - excluded_count}")

if __name__ == "__main__":
    test_filtering_logic()
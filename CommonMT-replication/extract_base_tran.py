"""
Extract base_translation from JSON files and extract just the English translation
"""

import os
import json
import re
import sys


# ===== CONFIGURATION =====
INPUT_DIR = "./hindi-english-output-claude-sonnet-4-5-20250929"  # Directory with JSON files
# =========================


def extract_english_from_base_translation(base_translation):
    """
    Extract the actual English translation from base_translation field.
    Handles various formats like:
    - "The translation is: \"text\""
    - "The translation is:\n\n\"text\""
    - "The translation is:\n\n\"text1\" or \"text2\""
    - Just "text"
    """
    if not base_translation:
        return ""
    
    # Pattern 1: Extract everything after "is:" or similar markers
    # This handles cases with multiple quoted options
    after_marker_pattern = r'(?:is|are):\s*\n*\s*(.+?)(?:\n\nDepending|\n\nNote:|\n\nThis|$)'
    match = re.search(after_marker_pattern, base_translation, re.DOTALL | re.IGNORECASE)
    
    if match:
        extracted = match.group(1).strip()
        
        # Check if there are multiple options with "or"
        # e.g., "text1" or "text2" or "text3"
        quote_pattern = r'"([^"]+)"'
        quoted_options = re.findall(quote_pattern, extracted)
        
        if quoted_options:
            # Return first option (usually the most direct translation)
            return quoted_options[0].strip()
        
        # If no quotes, clean up and return
        # Remove extra context after "or", "Depending", etc.
        extracted = re.split(r'\s+or\s+|\bDepending\b|\bNote:', extracted)[0]
        extracted = re.sub(r'^["\'\s]+|["\'\s]+$', '', extracted)
        return extracted.strip()
    
    # Pattern 2: Find all quoted text (fallback)
    quote_pattern = r'["\']([^"\']+)["\']'
    matches = re.findall(quote_pattern, base_translation)
    
    if matches:
        # Return the first quoted text (usually the main translation)
        return matches[0].strip()
    
    # Pattern 3: If nothing else works, return the whole thing cleaned up
    cleaned = base_translation.strip()
    
    # Remove common prefixes
    prefixes = [
        "The translation from Hindi to English is",
        "The translation of", 
        "Translation:",
        "The Hindi text",
        "translates to English as",
        "to English is"
    ]
    for prefix in prefixes:
        if prefix.lower() in cleaned.lower():
            # Find the prefix location and take everything after it
            idx = cleaned.lower().find(prefix.lower())
            cleaned = cleaned[idx + len(prefix):]
    
    # Remove everything after "Depending", "Note:", etc.
    cleaned = re.split(r'\n\nDepending|\n\nNote:|\n\nThis could', cleaned)[0]
    
    # Clean up quotes, colons, and extra whitespace
    cleaned = re.sub(r'^[:\s"\'\n]+|[:\s"\'\n]+$', '', cleaned)
    
    return cleaned.strip()


def extract_base_translations(output_file):
    """Extract base_translation from all JSON files"""
    
    # Get all JSON files (excluding config files)
    json_files = []
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.json') and not filename.endswith('-config.json'):
            json_files.append(filename)
    
    # Sort by ID number
    json_files.sort(key=lambda x: int(x.replace('.json', '')))
    
    print(f"Found {len(json_files)} JSON files in {INPUT_DIR}")
    
    # Extract base translations
    translations = []
    successful = 0
    failed = 0
    
    for filename in json_files:
        filepath = os.path.join(INPUT_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            base_translation = data.get('base_translation', '')
            source = data.get('source', '')
            
            if base_translation:
                # Extract just the English translation part
                english_translation = extract_english_from_base_translation(base_translation)
                translations.append(english_translation)
                successful += 1
            else:
                translations.append("")
                failed += 1
                print(f"⚠ {filename}: No base translation")
                print(f"  Source: {source[:50]}...")
                
        except Exception as e:
            print(f"✗ Error reading {filename}: {e}")
            translations.append("")
            failed += 1
    
    # Write to output file
    with open(output_file, 'w', encoding='utf-8') as f:
        for translation in translations:
            f.write(translation + '\n')
    
    print(f"\n{'='*50}")
    print(f"✓ Extraction complete!")
    print(f"{'='*50}")
    print(f"  Successful extractions: {successful}")
    print(f"  Failed/Missing: {failed}")
    print(f"  Total: {len(translations)}")
    print(f"  Output saved to: {output_file}")
    
    # Show a few examples
    if translations:
        print(f"\n📝 First 3 extracted translations:")
        for i, trans in enumerate(translations[:3]):
            print(f"  {i}: {trans}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_base_translations.py <output_file>")
        print("Example: python extract_base_translations.py baseline-output.txt")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found!")
        print("Please edit the INPUT_DIR variable in the script.")
        sys.exit(1)
    
    extract_base_translations(output_file)
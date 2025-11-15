"""
Simple script to extract debate_translation from all JSON output files
No command-line arguments needed - just edit the config below
"""

import os
import json
import sys

# ===== CONFIGURATION =====
INPUT_DIR = "./hindi-english-output-claude-sonnet-4-5-20250929"  # Directory with JSON files
# =========================

def extract_translations(output_file):
    """Extract debate_translation from all JSON files"""
    
    # Get all JSON files (excluding config files)
    json_files = []
    for filename in os.listdir(INPUT_DIR):
        if filename.endswith('.json') and not filename.endswith('-config.json'):
            json_files.append(filename)
    
    # Sort by ID number
    json_files.sort(key=lambda x: int(x.replace('.json', '')))
    
    print(f"Found {len(json_files)} JSON files in {INPUT_DIR}")
    
    # Extract translations
    translations = []
    successful = 0
    failed = 0
    
    for filename in json_files:
        filepath = os.path.join(INPUT_DIR, filename)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            debate_translation = data.get('debate_translation', '')
            success = data.get('success', False)
            source = data.get('source', '')
            
            if success and debate_translation:
                translations.append(debate_translation)
                successful += 1
            else:
                # If no debate translation, use base translation as fallback
                base_translation = data.get('base_translation', '')
                translations.append(base_translation)
                failed += 1
                print(f"{filename}: No debate translation (using base)")
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
    print(f"  Successful translations: {successful}")
    print(f"  Failed/Missing: {failed}")
    print(f"  Total: {len(translations)}")
    print(f"  Output saved to: {output_file}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python extract_translations_simple.py <output_file>")
        print("Example: python extract_translations_simple.py claude-3-haiku-20240307-output.txt")
        sys.exit(1)
    
    output_file = sys.argv[1]
    
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Input directory '{INPUT_DIR}' not found!")
        print("Please edit the INPUT_DIR variable in the script.")
        sys.exit(1)
    
    extract_translations(output_file)
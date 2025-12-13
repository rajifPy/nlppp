#!/usr/bin/env python3
"""
Script untuk convert format JSON rules atau validate existing rules
"""

import json
import os
from pathlib import Path
from typing import Dict, List

SDG_LABELS = [
    "No Poverty", "Zero Hunger", "Good Health and Well-being", "Quality Education",
    "Gender Equality", "Clean Water and Sanitation", "Affordable and Clean Energy",
    "Decent Work and Economic Growth", "Industry, Innovation and Infrastructure",
    "Reduced Inequality", "Sustainable Cities and Communities",
    "Responsible Consumption and Production", "Climate Action", "Life Below Water",
    "Life on Land", "Peace, Justice and Strong Institutions", "Partnerships for the Goals"
]


def validate_include_exclude_format(json_data: Dict) -> bool:
    """
    Validate format include/exclude
    """
    if "include" not in json_data:
        print("  ✗ Missing 'include' field")
        return False
    
    include = json_data["include"]
    if not isinstance(include, dict):
        print("  ✗ 'include' must be a dict")
        return False
    
    # Check fields
    valid_fields = ["TITLE_ABS", "AUTHKEY", "TITLE_ABS_KEY"]
    for field in include.keys():
        if field not in valid_fields:
            print(f"  ⚠️ Unknown field in include: {field}")
    
    if "exclude" in json_data:
        exclude = json_data["exclude"]
        if not isinstance(exclude, dict):
            print("  ✗ 'exclude' must be a dict")
            return False
    
    return True


def analyze_rule_file(filepath: Path) -> Dict:
    """
    Analyze single rule file
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        stats = {
            "valid": False,
            "format": "unknown",
            "include_count": 0,
            "exclude_count": 0,
            "fields": [],
            "errors": []
        }
        
        # Check format
        if "include" in data:
            stats["format"] = "include_exclude"
            stats["valid"] = validate_include_exclude_format(data)
            
            # Count keywords
            include = data.get("include", {})
            exclude = data.get("exclude", {})
            
            for field, keywords in include.items():
                stats["include_count"] += len(keywords)
                if field not in stats["fields"]:
                    stats["fields"].append(field)
            
            for field, keywords in exclude.items():
                stats["exclude_count"] += len(keywords)
        
        elif "keywords" in data:
            stats["format"] = "simple"
            stats["valid"] = True
            stats["include_count"] = len(data.get("keywords", []))
            stats["exclude_count"] = 0
        
        else:
            stats["errors"].append("Unknown format")
        
        return stats
        
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "format": "error",
            "errors": [f"JSON decode error: {str(e)}"]
        }
    except Exception as e:
        return {
            "valid": False,
            "format": "error",
            "errors": [f"Error: {str(e)}"]
        }


def convert_simple_to_include_exclude(simple_json: Dict) -> Dict:
    """
    Convert simple format to include/exclude format
    
    Simple format:
    {
      "sdg": 1,
      "title": "No Poverty",
      "keywords": [...],
      "phrases": [...],
      "patterns": [...]
    }
    
    To:
    {
      "include": {
        "TITLE_ABS": [...],
        "AUTHKEY": [...],
        "TITLE_ABS_KEY": []
      },
      "exclude": {
        "TITLE_ABS": [],
        "AUTHKEY": [],
        "TITLE_ABS_KEY": []
      }
    }
    """
    keywords = simple_json.get("keywords", [])
    phrases = simple_json.get("phrases", [])
    patterns = simple_json.get("patterns", [])
    
    # Combine all
    all_keywords = keywords + phrases + patterns
    
    return {
        "include": {
            "TITLE_ABS": all_keywords,
            "AUTHKEY": all_keywords,
            "TITLE_ABS_KEY": []
        },
        "exclude": {
            "TITLE_ABS": [],
            "AUTHKEY": [],
            "TITLE_ABS_KEY": []
        }
    }


def check_duplicates(keywords: List[str]) -> List[str]:
    """
    Find duplicate keywords
    """
    seen = set()
    duplicates = []
    
    for kw in keywords:
        kw_lower = kw.lower()
        if kw_lower in seen:
            duplicates.append(kw)
        seen.add(kw_lower)
    
    return duplicates


def analyze_all_rules(rules_dir: str = "models/rules"):
    """
    Analyze all rule files in directory
    """
    rules_path = Path(rules_dir)
    
    if not rules_path.exists():
        print(f"❌ Directory not found: {rules_dir}")
        return
    
    print("="*70)
    print("RULE FILES ANALYSIS")
    print("="*70)
    
    total_include = 0
    total_exclude = 0
    valid_files = 0
    invalid_files = 0
    
    for sdg_num in range(1, 18):
        # Try different formats
        json_file = rules_path / f"SDG{sdg_num:02d}.json"
        if not json_file.exists():
            json_file = rules_path / f"sdg_{sdg_num}.json"
        
        if not json_file.exists():
            print(f"\n⚠️  SDG {sdg_num:2d}: File not found")
            invalid_files += 1
            continue
        
        print(f"\n📄 SDG {sdg_num:2d}: {SDG_LABELS[sdg_num-1]}")
        print(f"   File: {json_file.name}")
        
        stats = analyze_rule_file(json_file)
        
        if stats["valid"]:
            print(f"   ✓ Format: {stats['format']}")
            print(f"   ✓ Include keywords: {stats['include_count']}")
            print(f"   ✓ Exclude keywords: {stats['exclude_count']}")
            print(f"   ✓ Fields: {', '.join(stats['fields'])}")
            
            total_include += stats['include_count']
            total_exclude += stats['exclude_count']
            valid_files += 1
            
            # Check for issues
            if stats['include_count'] == 0:
                print(f"   ⚠️  WARNING: No include keywords!")
            elif stats['include_count'] < 20:
                print(f"   ⚠️  WARNING: Very few keywords (<20)")
            
            # Check duplicates if possible
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if "include" in data:
                        for field, keywords in data["include"].items():
                            dupes = check_duplicates(keywords)
                            if dupes:
                                print(f"   ⚠️  Duplicates in {field}: {len(dupes)}")
            except:
                pass
        else:
            print(f"   ✗ Invalid!")
            for error in stats.get("errors", []):
                print(f"     - {error}")
            invalid_files += 1
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Valid files:   {valid_files}/17")
    print(f"Invalid files: {invalid_files}/17")
    print(f"Total include keywords: {total_include:,}")
    print(f"Total exclude keywords: {total_exclude:,}")
    print(f"Average include per SDG: {total_include/max(valid_files,1):.0f}")
    print("="*70)


def create_template_rule(sdg_num: int, output_file: str):
    """
    Create template rule file
    """
    template = {
        "include": {
            "TITLE_ABS": [
                f"keyword1 for sdg {sdg_num}",
                f"keyword2 for sdg {sdg_num}",
                f"phrase for sdg {sdg_num}"
            ],
            "AUTHKEY": [
                f"author keyword for sdg {sdg_num}"
            ],
            "TITLE_ABS_KEY": []
        },
        "exclude": {
            "TITLE_ABS": [
                "irrelevant keyword",
                "false positive term"
            ],
            "AUTHKEY": [],
            "TITLE_ABS_KEY": []
        }
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(template, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Template created: {output_file}")


def merge_keywords(file1: str, file2: str, output_file: str):
    """
    Merge keywords from two rule files
    """
    try:
        with open(file1, 'r', encoding='utf-8') as f:
            data1 = json.load(f)
        with open(file2, 'r', encoding='utf-8') as f:
            data2 = json.load(f)
        
        merged = {
            "include": {
                "TITLE_ABS": [],
                "AUTHKEY": [],
                "TITLE_ABS_KEY": []
            },
            "exclude": {
                "TITLE_ABS": [],
                "AUTHKEY": [],
                "TITLE_ABS_KEY": []
            }
        }
        
        # Merge include
        for field in ["TITLE_ABS", "AUTHKEY", "TITLE_ABS_KEY"]:
            keywords1 = data1.get("include", {}).get(field, [])
            keywords2 = data2.get("include", {}).get(field, [])
            # Remove duplicates while preserving order
            seen = set()
            for kw in keywords1 + keywords2:
                kw_lower = kw.lower()
                if kw_lower not in seen:
                    merged["include"][field].append(kw)
                    seen.add(kw_lower)
        
        # Merge exclude
        for field in ["TITLE_ABS", "AUTHKEY", "TITLE_ABS_KEY"]:
            keywords1 = data1.get("exclude", {}).get(field, [])
            keywords2 = data2.get("exclude", {}).get(field, [])
            seen = set()
            for kw in keywords1 + keywords2:
                kw_lower = kw.lower()
                if kw_lower not in seen:
                    merged["exclude"][field].append(kw)
                    seen.add(kw_lower)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(merged, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Merged rules saved to: {output_file}")
        print(f"  Include TITLE_ABS: {len(merged['include']['TITLE_ABS'])} keywords")
        print(f"  Exclude TITLE_ABS: {len(merged['exclude']['TITLE_ABS'])} keywords")
        
    except Exception as e:
        print(f"❌ Error merging: {e}")


def main():
    import sys
    
    if len(sys.argv) < 2:
        print("""
Usage:
  python convert_rules.py analyze [rules_dir]    - Analyze all rule files
  python convert_rules.py template <sdg> <file>  - Create template
  python convert_rules.py merge <f1> <f2> <out>  - Merge two files
        """)
        return
    
    command = sys.argv[1]
    
    if command == "analyze":
        rules_dir = sys.argv[2] if len(sys.argv) > 2 else "models/rules"
        analyze_all_rules(rules_dir)
    
    elif command == "template":
        if len(sys.argv) < 4:
            print("Usage: convert_rules.py template <sdg_number> <output_file>")
            return
        sdg_num = int(sys.argv[2])
        output_file = sys.argv[3]
        create_template_rule(sdg_num, output_file)
    
    elif command == "merge":
        if len(sys.argv) < 5:
            print("Usage: convert_rules.py merge <file1> <file2> <output>")
            return
        merge_keywords(sys.argv[2], sys.argv[3], sys.argv[4])
    
    else:
        print(f"Unknown command: {command}")


if __name__ == "__main__":
    main()
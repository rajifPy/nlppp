import json
import os
import re
import logging
from typing import List, Dict, Set
from pathlib import Path

logger = logging.getLogger(__name__)

# ===== SDG LABELS =====
SDG_LABELS = [
    "No Poverty",
    "Zero Hunger",
    "Good Health and Well-being",
    "Quality Education",
    "Gender Equality",
    "Clean Water and Sanitation",
    "Affordable and Clean Energy",
    "Decent Work and Economic Growth",
    "Industry, Innovation and Infrastructure",
    "Reduced Inequality",
    "Sustainable Cities and Communities",
    "Responsible Consumption and Production",
    "Climate Action",
    "Life Below Water",
    "Life on Land",
    "Peace, Justice and Strong Institutions",
    "Partnerships for the Goals"
]


class RuleEngine:
    """
    Rule-based engine untuk klasifikasi SDG menggunakan JSON rules
    Mendukung format:
    1. sdg_N.json (lowercase dengan underscore)
    2. SDGNN.json (uppercase dengan nomor 2 digit)
    """
    
    def __init__(self, rules_dir: str = "models/rules"):
        self.rules_dir = rules_dir
        self.rules = {}
        self.is_loaded = False
        
    def load_rules(self) -> bool:
        """
        Load semua rule JSON dari folder rules
        Mencoba berbagai format nama file
        
        Returns:
            bool: True jika berhasil load minimal 1 rule, False jika gagal
        """
        try:
            rules_path = Path(self.rules_dir)
            
            if not rules_path.exists():
                logger.error(f"Rules directory not found: {self.rules_dir}")
                return False
            
            loaded_count = 0
            
            for sdg_num in range(1, 18):  # SDG 1-17
                rule_data = None
                
                # Try different naming conventions
                possible_names = [
                    f"sdg_{sdg_num}.json",           # sdg_1.json
                    f"SDG{sdg_num:02d}.json",        # SDG01.json
                    f"sdg{sdg_num:02d}.json",        # sdg01.json
                    f"SDG{sdg_num}.json",            # SDG1.json
                ]
                
                for filename in possible_names:
                    json_file = rules_path / filename
                    if json_file.exists():
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                rule_data = json.load(f)
                                self.rules[sdg_num] = rule_data
                                loaded_count += 1
                                logger.info(f"✓ Loaded rules for SDG {sdg_num} from {filename}")
                                break  # Stop after successful load
                        except json.JSONDecodeError as e:
                            logger.error(f"JSON decode error in {filename}: {e}")
                        except Exception as e:
                            logger.error(f"Error loading {filename}: {e}")
                
                if sdg_num not in self.rules:
                    logger.warning(f"⚠ No rules file found for SDG {sdg_num}")
            
            if loaded_count > 0:
                self.is_loaded = True
                logger.info(f"✓ Successfully loaded {loaded_count}/17 SDG rules")
                return True
            else:
                logger.error("✗ No rules loaded")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load rules: {str(e)}")
            self.is_loaded = False
            return False
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text untuk matching
        """
        # Lowercase
        text = text.lower()
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def match_keywords(self, text: str, keywords: List[str]) -> Set[str]:
        """
        Match keywords dalam teks (case-insensitive, mendukung wildcard *)
        """
        matched = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Handle wildcard *
            if '*' in keyword_lower:
                # Convert wildcard to regex pattern
                pattern = keyword_lower.replace('*', '.*')
                pattern = r'\b' + pattern + r'\b'
                try:
                    if re.search(pattern, text):
                        matched.add(keyword)
                except re.error:
                    # Fallback to simple contains
                    if keyword_lower.replace('*', '') in text:
                        matched.add(keyword)
            else:
                # Exact word boundary match
                pattern = r'\b' + re.escape(keyword_lower) + r'\b'
                if re.search(pattern, text):
                    matched.add(keyword)
        
        return matched
    
    def analyze(self, text: str, match_field: str = 'all', min_matches: int = 1) -> List[Dict]:
        """
        Analyze text dengan rules
        
        Args:
            text: Input text
            match_field: Field untuk match ("TITLE_ABS", "AUTHKEY", "TITLE_ABS_KEY", "all")
            min_matches: Minimum number of matches untuk include SDG
            
        Returns:
            List[Dict]: Matched SDGs dengan details
        """
        if not self.is_loaded:
            logger.error("Rules not loaded!")
            return []
        
        # Normalize text
        normalized_text = self.normalize_text(text)
        
        results = []
        
        # Check each SDG
        for sdg_num, rule in self.rules.items():
            matched_keywords = set()
            
            # Get include keywords based on field
            include_data = rule.get('include', {})
            
            if match_field == 'all':
                # Match across all fields
                for field, keywords in include_data.items():
                    if isinstance(keywords, list):
                        matched_keywords.update(
                            self.match_keywords(normalized_text, keywords)
                        )
            elif match_field in include_data:
                # Match specific field
                keywords = include_data[match_field]
                if isinstance(keywords, list):
                    matched_keywords = self.match_keywords(normalized_text, keywords)
            
            # Check exclude keywords
            exclude_data = rule.get('exclude', {})
            excluded_keywords = set()
            
            for field, keywords in exclude_data.items():
                if isinstance(keywords, list):
                    excluded_keywords.update(
                        self.match_keywords(normalized_text, keywords)
                    )
            
            # Remove excluded keywords from matches
            final_matches = matched_keywords - excluded_keywords
            match_count = len(final_matches)
            
            # Only include if meets minimum threshold
            if match_count >= min_matches:
                # Calculate confidence based on matches
                base_confidence = min(100, match_count * 10 + 20)
                
                results.append({
                    "sdg": f"SDG {sdg_num}: {SDG_LABELS[sdg_num-1]}",
                    "matched_rules": sorted(list(final_matches))[:20],  # Limit to top 20
                    "match_count": match_count,
                    "confidence": round(base_confidence, 2),
                    "source": "rule_based",
                    "excluded_count": len(excluded_keywords)
                })
        
        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return results[:10]  # Return top 10
    
    def get_rules_summary(self) -> Dict:
        """
        Dapatkan summary dari loaded rules
        """
        summary = {
            "total_sdgs": len(self.rules),
            "is_loaded": self.is_loaded,
            "sdgs": {}
        }
        
        for sdg_num, rule in self.rules.items():
            include_data = rule.get('include', {})
            exclude_data = rule.get('exclude', {})
            
            total_include = sum(len(keywords) for keywords in include_data.values() if isinstance(keywords, list))
            total_exclude = sum(len(keywords) for keywords in exclude_data.values() if isinstance(keywords, list))
            
            summary["sdgs"][sdg_num] = {
                "title": SDG_LABELS[sdg_num-1],
                "include_keywords": total_include,
                "exclude_keywords": total_exclude,
                "fields": list(include_data.keys())
            }
        
        return summary
    
    def get_sdg_keywords(self, sdg_num: int) -> Dict:
        """
        Dapatkan keywords untuk SDG tertentu
        
        Args:
            sdg_num: SDG number (1-17)
            
        Returns:
            Dict: Include and exclude keywords by field
        """
        if sdg_num in self.rules:
            return {
                "include": self.rules[sdg_num].get('include', {}),
                "exclude": self.rules[sdg_num].get('exclude', {})
            }
        return {"include": {}, "exclude": {}}


# ===== CONTOH PENGGUNAAN =====
if __name__ == "__main__":
    # Test rule engine
    engine = RuleEngine("models/rules")
    
    if engine.load_rules():
        print("✓ Rules loaded successfully!")
        print(f"\nRules summary: {json.dumps(engine.get_rules_summary(), indent=2)}")
        
        # Test analysis
        test_text = """
        This research focuses on renewable energy solutions for sustainable development.
        We explore solar power and wind energy systems to reduce carbon emissions
        and combat climate change in urban communities.
        """
        
        results = engine.analyze(test_text, min_matches=2)
        
        print("\n" + "="*60)
        print("RULE MATCHING RESULTS")
        print("="*60)
        
        for result in results:
            print(f"\n{result['sdg']}")
            print(f"  Confidence: {result['confidence']}%")
            print(f"  Matches: {result['match_count']}")
            print(f"  Matched rules: {', '.join(result['matched_rules'][:5])}")
            if result['excluded_count'] > 0:
                print(f"  Excluded: {result['excluded_count']} keywords")
    else:
        print("✗ Failed to load rules!")

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
    Format JSON:
    {
      "include": {
        "TITLE_ABS": [...keywords...],
        "AUTHKEY": [...keywords...],
        "TITLE_ABS_KEY": [...keywords...]
      },
      "exclude": {
        "TITLE_ABS": [...keywords...],
        "AUTHKEY": [...keywords...],
        "TITLE_ABS_KEY": [...keywords...]
      }
    }
    """
    
    def __init__(self, rules_dir: str = "models/rules"):
        self.rules_dir = rules_dir
        self.rules = {}
        self.is_loaded = False
        
    def load_rules(self) -> bool:
        """
        Load semua rule JSON dari folder rules
        
        Expected JSON format:
        {
            "sdg": 1,
            "title": "No Poverty",
            "keywords": ["poverty", "poor", "income"],
            "phrases": ["extreme poverty", "social protection"],
            "patterns": ["poverty.*reduction", "income.*inequality"],
            "weight": 1.0,
            "synonyms": {
                "poverty": ["deprivation", "destitution"],
                "poor": ["impoverished", "needy"]
            }
        }
        
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            rules_path = Path(self.rules_dir)
            
            if not rules_path.exists():
                logger.error(f"Rules directory not found: {self.rules_dir}")
                return False
            
            # Load each JSON file
            loaded_count = 0
            for sdg_num in range(1, 18):  # SDG 1-17
                json_file = rules_path / f"sdg_{sdg_num}.json"
                
                if json_file.exists():
                    with open(json_file, 'r', encoding='utf-8') as f:
                        rule_data = json.load(f)
                        self.rules[sdg_num] = rule_data
                        loaded_count += 1
                        logger.info(f"Loaded rules for SDG {sdg_num}")
                else:
                    logger.warning(f"Rules file not found: {json_file}")
            
            if loaded_count > 0:
                self.is_loaded = True
                logger.info(f"Successfully loaded {loaded_count} SDG rules")
                return True
            else:
                logger.error("No rules loaded")
                return False
                
        except Exception as e:
            logger.error(f"Failed to load rules: {str(e)}")
            self.is_loaded = False
            return False
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text untuk matching
        
        Args:
            text: Input text
            
        Returns:
            str: Normalized text
        """
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters (optional)
        # text = re.sub(r'[^\w\s]', '', text)
        
        return text.strip()
    
    def match_keywords(self, text: str, keywords: List[str]) -> Set[str]:
        """
        Match keywords dalam teks
        
        Args:
            text: Normalized text
            keywords: List of keywords
            
        Returns:
            Set[str]: Matched keywords
        """
        matched = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            
            # Exact match atau word boundary match
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, text):
                matched.add(keyword)
        
        return matched
    
    def match_phrases(self, text: str, phrases: List[str]) -> Set[str]:
        """
        Match multi-word phrases dalam teks
        
        Args:
            text: Normalized text
            phrases: List of phrases
            
        Returns:
            Set[str]: Matched phrases
        """
        matched = set()
        
        for phrase in phrases:
            phrase_lower = phrase.lower()
            if phrase_lower in text:
                matched.add(phrase)
        
        return matched
    
    def match_patterns(self, text: str, patterns: List[str]) -> Set[str]:
        """
        Match regex patterns dalam teks
        
        Args:
            text: Normalized text
            patterns: List of regex patterns
            
        Returns:
            Set[str]: Matched patterns
        """
        matched = set()
        
        for pattern in patterns:
            try:
                if re.search(pattern, text, re.IGNORECASE):
                    matched.add(pattern)
            except re.error as e:
                logger.warning(f"Invalid regex pattern '{pattern}': {e}")
        
        return matched
    
    def match_with_synonyms(self, text: str, keyword: str, synonyms: List[str]) -> bool:
        """
        Match keyword dengan synonym-nya
        
        Args:
            text: Normalized text
            keyword: Main keyword
            synonyms: List of synonyms
            
        Returns:
            bool: True if matched
        """
        # Check main keyword
        if keyword.lower() in text:
            return True
        
        # Check synonyms
        for syn in synonyms:
            if syn.lower() in text:
                return True
        
        return False
    
    def analyze(self, text: str, use_synonyms: bool = True, 
                min_matches: int = 1) -> List[Dict]:
        """
        Analyze text dengan rules
        
        Args:
            text: Input text
            use_synonyms: Whether to use synonyms
            min_matches: Minimum number of matches to include SDG
            
        Returns:
            List[Dict]: Matched SDGs with details
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
            matched_phrases = set()
            matched_patterns = set()
            
            # Match keywords
            if 'keywords' in rule:
                matched_keywords = self.match_keywords(
                    normalized_text, 
                    rule['keywords']
                )
            
            # Match phrases
            if 'phrases' in rule:
                matched_phrases = self.match_phrases(
                    normalized_text,
                    rule['phrases']
                )
            
            # Match patterns
            if 'patterns' in rule:
                matched_patterns = self.match_patterns(
                    normalized_text,
                    rule['patterns']
                )
            
            # Match with synonyms
            if use_synonyms and 'synonyms' in rule:
                for keyword, synonyms in rule['synonyms'].items():
                    if self.match_with_synonyms(normalized_text, keyword, synonyms):
                        matched_keywords.add(keyword)
            
            # Combine all matches
            all_matches = matched_keywords | matched_phrases | matched_patterns
            match_count = len(all_matches)
            
            # Only include if meets minimum threshold
            if match_count >= min_matches:
                # Calculate confidence based on matches and weight
                weight = rule.get('weight', 1.0)
                base_confidence = min(100, match_count * 15 * weight)
                
                results.append({
                    "sdg": f"SDG {sdg_num}: {rule.get('title', SDG_LABELS[sdg_num-1])}",
                    "matched_rules": list(all_matches),
                    "match_count": match_count,
                    "confidence": round(base_confidence, 2),
                    "source": "rule_based",
                    "details": {
                        "keywords": list(matched_keywords),
                        "phrases": list(matched_phrases),
                        "patterns": list(matched_patterns)
                    }
                })
        
        # Sort by confidence
        results.sort(key=lambda x: x["confidence"], reverse=True)
        
        return results[:10]  # Return top 10
    
    def get_rules_summary(self) -> Dict:
        """
        Dapatkan summary dari loaded rules
        
        Returns:
            Dict: Rules summary
        """
        summary = {
            "total_sdgs": len(self.rules),
            "is_loaded": self.is_loaded,
            "sdgs": {}
        }
        
        for sdg_num, rule in self.rules.items():
            summary["sdgs"][sdg_num] = {
                "title": rule.get('title', ''),
                "keyword_count": len(rule.get('keywords', [])),
                "phrase_count": len(rule.get('phrases', [])),
                "pattern_count": len(rule.get('patterns', [])),
                "has_synonyms": 'synonyms' in rule
            }
        
        return summary
    
    def get_sdg_keywords(self, sdg_num: int) -> List[str]:
        """
        Dapatkan keywords untuk SDG tertentu
        
        Args:
            sdg_num: SDG number (1-17)
            
        Returns:
            List[str]: Keywords
        """
        if sdg_num in self.rules:
            return self.rules[sdg_num].get('keywords', [])
        return []


# ===== CONTOH PENGGUNAAN =====
if __name__ == "__main__":
    # Test rule engine
    engine = RuleEngine("models/rules")
    
    if engine.load_rules():
        print("Rules loaded successfully!")
        print(f"\nRules summary: {json.dumps(engine.get_rules_summary(), indent=2)}")
        
        # Test analysis
        test_text = """
        This research focuses on renewable energy solutions for sustainable development.
        We explore solar power and wind energy systems to reduce carbon emissions
        and combat climate change in urban communities.
        """
        
        results = engine.analyze(test_text)
        
        print("\n" + "="*60)
        print("RULE MATCHING RESULTS")
        print("="*60)
        
        for result in results:
            print(f"\n{result['sdg']}")
            print(f"  Confidence: {result['confidence']}%")
            print(f"  Matches: {result['match_count']}")
            print(f"  Matched rules: {', '.join(result['matched_rules'][:5])}")
    else:
        print("Failed to load rules!")
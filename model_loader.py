import torch
import torch.nn as nn
import logging
from typing import List, Dict, Tuple
import numpy as np
import os

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


class SDGModelLoader:
    """
    Loader untuk model PyTorch (.pt) untuk klasifikasi SDG
    """
    
    def __init__(self, model_path: str = "models/sdg_model.pt"):
        self.model_path = model_path
        self.model = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.is_loaded = False
        
    def load_model(self) -> bool:
        """
        Load model PyTorch dari file .pt
        
        Returns:
            bool: True jika berhasil, False jika gagal
        """
        try:
            # Check if file exists
            if not os.path.exists(self.model_path):
                logger.error(f"Model file not found: {self.model_path}")
                logger.warning("Model will not be available. Using fallback prediction.")
                self.is_loaded = False
                return False
            
            logger.info(f"Loading PyTorch model from {self.model_path}")
            
            # Load model state dict atau full model
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Jika checkpoint adalah dict dengan 'model' atau 'state_dict'
            if isinstance(checkpoint, dict):
                if 'model' in checkpoint:
                    self.model = checkpoint['model']
                elif 'state_dict' in checkpoint:
                    # Anda perlu mendefinisikan arsitektur model di sini
                    logger.warning("Model requires architecture definition")
                    self.model = checkpoint
                else:
                    self.model = checkpoint
            else:
                # Checkpoint langsung adalah model
                self.model = checkpoint
            
            # Set model ke evaluation mode
            if hasattr(self.model, 'eval'):
                self.model.eval()
                self.model.to(self.device)
            
            self.is_loaded = True
            logger.info(f"Model loaded successfully on {self.device}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            logger.warning("Model will not be available. Using fallback prediction.")
            self.is_loaded = False
            return False
    
    def preprocess_text(self, text: str) -> torch.Tensor:
        """
        Preprocess teks untuk input model
        
        Args:
            text: Input text
            
        Returns:
            torch.Tensor: Preprocessed input
        """
        # FALLBACK: Return dummy tensor jika model tidak loaded
        logger.warning("Using dummy preprocessing - model not available!")
        return torch.randn(1, 512)
    
    def predict(self, text: str, threshold: float = 0.05) -> List[Dict]:
        """
        Prediksi SDG dari teks
        
        Args:
            text: Input text untuk klasifikasi
            threshold: Minimum confidence untuk menampilkan hasil
            
        Returns:
            List[Dict]: List of predictions dengan SDG dan confidence
        """
        if not self.is_loaded:
            logger.warning("Model not loaded! Using fallback keyword-based prediction.")
            return self._fallback_predict(text, threshold)
        
        try:
            # Preprocess input
            inputs = self.preprocess_text(text)
            
            # Jika inputs adalah dict (dari transformers)
            if isinstance(inputs, dict):
                inputs = {k: v.to(self.device) for k, v in inputs.items()}
            else:
                inputs = inputs.to(self.device)
            
            # Inference
            with torch.no_grad():
                if isinstance(inputs, dict):
                    outputs = self.model(**inputs)
                else:
                    outputs = self.model(inputs)
                
                # Get probabilities
                if isinstance(outputs, tuple):
                    logits = outputs[0]
                elif isinstance(outputs, dict):
                    logits = outputs['logits']
                else:
                    logits = outputs
                
                # Apply sigmoid for multi-label
                probs = torch.sigmoid(logits)
                probs = probs.cpu().numpy()[0]
            
            # Format hasil
            predictions = []
            for idx, prob in enumerate(probs):
                if prob > threshold:
                    predictions.append({
                        "sdg": f"SDG {idx + 1}: {SDG_LABELS[idx]}",
                        "confidence": float(prob * 100),
                        "source": "pytorch_model"
                    })
            
            # Sort by confidence
            predictions.sort(key=lambda x: x["confidence"], reverse=True)
            
            # Return top 5
            return predictions[:5] if predictions else self._fallback_predict(text, threshold)
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return self._fallback_predict(text, threshold)
    
    def _fallback_predict(self, text: str, threshold: float = 0.05) -> List[Dict]:
        """
        Fallback prediction menggunakan keyword matching sederhana
        
        Args:
            text: Input text
            threshold: Minimum confidence (not used in fallback)
            
        Returns:
            List[Dict]: Fallback predictions
        """
        text_lower = text.lower()
        
        # Simple keyword mapping untuk setiap SDG
        sdg_keywords = {
            1: ["poverty", "poor", "inequality", "income"],
            2: ["hunger", "food", "nutrition", "agriculture"],
            3: ["health", "disease", "medicine", "healthcare"],
            4: ["education", "school", "learning", "teacher"],
            5: ["gender", "women", "equality", "female"],
            6: ["water", "sanitation", "hygiene", "clean water"],
            7: ["energy", "renewable", "solar", "electricity"],
            8: ["employment", "work", "job", "economic growth"],
            9: ["infrastructure", "industry", "innovation", "technology"],
            10: ["inequality", "discrimination", "inclusion"],
            11: ["city", "urban", "community", "housing"],
            12: ["consumption", "production", "waste", "sustainable"],
            13: ["climate", "carbon", "emission", "global warming"],
            14: ["ocean", "marine", "sea", "fish"],
            15: ["forest", "biodiversity", "land", "ecosystem"],
            16: ["peace", "justice", "law", "institution"],
            17: ["partnership", "cooperation", "collaboration", "global"]
        }
        
        predictions = []
        
        for sdg_num, keywords in sdg_keywords.items():
            match_count = sum(1 for keyword in keywords if keyword in text_lower)
            if match_count > 0:
                # Calculate simple confidence based on matches
                confidence = min(100, (match_count / len(keywords)) * 100 + 20)
                predictions.append({
                    "sdg": f"SDG {sdg_num}: {SDG_LABELS[sdg_num-1]}",
                    "confidence": float(confidence),
                    "source": "keyword_fallback",
                    "note": f"Matched {match_count} keywords"
                })
        
        # Sort by confidence
        predictions.sort(key=lambda x: x["confidence"], reverse=True)
        
        # Return top 5 atau minimal 1
        if not predictions:
            # Jika tidak ada yang match, return default SDG 17
            predictions = [{
                "sdg": f"SDG 17: {SDG_LABELS[16]}",
                "confidence": 50.0,
                "source": "default_fallback",
                "note": "No specific keywords detected"
            }]
        
        return predictions[:5]
    
    def get_model_info(self) -> Dict:
        """
        Dapatkan informasi tentang model
        
        Returns:
            Dict: Model information
        """
        info = {
            "model_path": self.model_path,
            "is_loaded": self.is_loaded,
            "device": str(self.device),
            "num_labels": len(SDG_LABELS),
            "mode": "pytorch_model" if self.is_loaded else "keyword_fallback"
        }
        
        if self.model and hasattr(self.model, 'config'):
            info["model_type"] = getattr(self.model.config, 'model_type', 'unknown')
        
        return info


# ===== CONTOH PENGGUNAAN =====
if __name__ == "__main__":
    # Test model loader
    loader = SDGModelLoader("models/sdg_model.pt")
    
    if loader.load_model():
        print("✓ Model loaded successfully!")
    else:
        print("⚠ Model not loaded, using fallback mode")
    
    # Test prediction
    test_text = "This research focuses on renewable energy and sustainable development"
    predictions = loader.predict(test_text)
    
    print("\nPredictions:")
    for pred in predictions:
        note = f" ({pred['note']})" if 'note' in pred else ""
        print(f"  {pred['sdg']}: {pred['confidence']:.2f}% - {pred['source']}{note}")

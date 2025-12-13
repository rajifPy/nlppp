import torch
import torch.nn as nn
import logging
from typing import List, Dict, Tuple
import numpy as np

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
            logger.info(f"Loading PyTorch model from {self.model_path}")
            
            # Load model state dict atau full model
            checkpoint = torch.load(self.model_path, map_location=self.device)
            
            # Jika checkpoint adalah dict dengan 'model' atau 'state_dict'
            if isinstance(checkpoint, dict):
                if 'model' in checkpoint:
                    self.model = checkpoint['model']
                elif 'state_dict' in checkpoint:
                    # Anda perlu mendefinisikan arsitektur model di sini
                    # Contoh: self.model = YourModelClass()
                    # self.model.load_state_dict(checkpoint['state_dict'])
                    logger.warning("Model requires architecture definition")
                    # Untuk sementara, kita asumsikan checkpoint adalah model lengkap
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
            self.is_loaded = False
            return False
    
    def preprocess_text(self, text: str) -> torch.Tensor:
        """
        Preprocess teks untuk input model
        CATATAN: Sesuaikan dengan preprocessing yang Anda gunakan saat training
        
        Args:
            text: Input text
            
        Returns:
            torch.Tensor: Preprocessed input
        """
        # CONTOH PREPROCESSING - SESUAIKAN DENGAN MODEL ANDA
        # Ini hanya contoh, Anda harus menyesuaikan dengan:
        # 1. Tokenizer yang Anda gunakan (BERT, RoBERTa, dll)
        # 2. Max length
        # 3. Padding strategy
        
        # Jika menggunakan transformers tokenizer:
        # from transformers import AutoTokenizer
        # tokenizer = AutoTokenizer.from_pretrained('bert-base-uncased')
        # encoding = tokenizer(text, truncation=True, padding='max_length', 
        #                     max_length=512, return_tensors='pt')
        # return encoding
        
        # Untuk demonstrasi, kita return dummy tensor
        # GANTI INI dengan preprocessing yang sebenarnya!
        logger.warning("Using dummy preprocessing - replace with actual preprocessing!")
        return torch.randn(1, 512)  # Dummy tensor
    
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
            logger.error("Model not loaded!")
            return []
        
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
                # Sesuaikan dengan output model Anda
                if isinstance(outputs, tuple):
                    logits = outputs[0]
                elif isinstance(outputs, dict):
                    logits = outputs['logits']
                else:
                    logits = outputs
                
                # Apply sigmoid for multi-label atau softmax for single-label
                # Untuk multi-label classification (bisa multiple SDGs):
                probs = torch.sigmoid(logits)
                # Untuk single-label classification:
                # probs = torch.softmax(logits, dim=-1)
                
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
            return predictions[:5]
            
        except Exception as e:
            logger.error(f"Prediction error: {str(e)}")
            return []
    
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
            "num_labels": len(SDG_LABELS)
        }
        
        if self.model and hasattr(self.model, 'config'):
            info["model_type"] = getattr(self.model.config, 'model_type', 'unknown')
        
        return info


# ===== CONTOH PENGGUNAAN =====
if __name__ == "__main__":
    # Test model loader
    loader = SDGModelLoader("models/best_model.pt")
    
    if loader.load_model():
        print("Model loaded successfully!")
        
        # Test prediction
        test_text = "This research focuses on renewable energy and sustainable development"
        predictions = loader.predict(test_text)
        
        print("\nPredictions:")
        for pred in predictions:
            print(f"  {pred['sdg']}: {pred['confidence']:.2f}%")
    else:
        print("Failed to load model!")
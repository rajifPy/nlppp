import os
import logging
import warnings
import joblib
from flask import Flask, request, jsonify, render_template, send_from_directory
from document_extractor import DocumentExtractor

# Suppress warnings
warnings.filterwarnings('ignore')

# ===== CONFIG =====
app = Flask(__name__, template_folder='templates')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

logging.basicConfig(level=logging.INFO)
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

# ===== GLOBAL VARIABLES =====
ml_model = None
MODEL_LOADED = False

# ===== LOAD MODEL =====
def load_model():
    global ml_model, MODEL_LOADED
    try:
        model_path = "SDG_Final_Pipeline.joblib"
        logger.info(f"Loading ML model from {model_path}")
        ml_model = joblib.load(model_path)
        MODEL_LOADED = True
        logger.info("Model loaded successfully!")
        return True
    except Exception as e:
        logger.error(f"Failed to load model: {str(e)}")
        return False

# Load model saat startup
load_model()

# ===== HELPER FUNCTIONS =====
def format_sdg_label(label: str):
    """Ubah nama SDG menjadi 'SDG X: Nama SDG'"""
    if label in SDG_LABELS:
        idx = SDG_LABELS.index(label) + 1
        return f"SDG {idx}: {label}"
    return label

def find_related_sdgs(text: str):
    """Temukan SDG terkait berdasarkan keyword matching"""
    text_lower = text.lower()
    related = []
    
    keyword_map = {
        "poverty": "No Poverty",
        "hunger": "Zero Hunger",
        "health": "Good Health and Well-being",
        "education": "Quality Education",
        "gender": "Gender Equality",
        "water": "Clean Water and Sanitation",
        "energy": "Affordable and Clean Energy",
        "economic": "Decent Work and Economic Growth",
        "innovation": "Industry, Innovation and Infrastructure",
        "inequality": "Reduced Inequality",
        "city": "Sustainable Cities and Communities",
        "consumption": "Responsible Consumption and Production",
        "climate": "Climate Action",
        "ocean": "Life Below Water",
        "forest": "Life on Land",
        "peace": "Peace, Justice and Strong Institutions",
        "partnership": "Partnerships for the Goals"
    }
    
    for keyword, sdg in keyword_map.items():
        if keyword in text_lower:
            related.append(format_sdg_label(sdg))
    
    return list(dict.fromkeys(related))[:5]

def predict_text(text: str):
    """Prediksi SDGs untuk satu teks, hasil dengan nomor SDG"""
    predictions = []
    
    if MODEL_LOADED and ml_model:
        try:
            probs = ml_model.predict_proba([text])[0]
            classes = ml_model.classes_
            for cls, score in zip(classes, probs):
                if score > 0.05:
                    predictions.append({
                        "sdg": format_sdg_label(cls),
                        "confidence": round(score * 100, 2),
                        "source": "ml_model"
                    })
            predictions.sort(key=lambda x: x["confidence"], reverse=True)
            predictions = predictions[:5]
        except Exception as e:
            logger.error(f"ML prediction failed: {str(e)}")
    
    # Keyword fallback
    keyword_results = find_related_sdgs(text)
    existing_sdgs = [p["sdg"] for p in predictions]
    for sdg in keyword_results:
        if sdg not in existing_sdgs:
            predictions.append({
                "sdg": sdg,
                "confidence": 60.0,
                "source": "keyword_matching"
            })
    
    # Fallback jika tidak ada prediksi
    if not predictions:
        predictions.append({
            "sdg": format_sdg_label("Partnerships for the Goals"),
            "confidence": 50.0,
            "source": "fallback",
            "note": "No specific SDG detected"
        })
    
    return predictions, keyword_results

# ===== ROUTES =====
@app.route('/')
def home():
    return render_template('index.html', 
                           model_loaded=MODEL_LOADED,
                           model_name="SDG_Final_Pipeline.joblib")

@app.route('/index.html')
def index():
    return home()

@app.route('/model-detection.html')
def model_detection():
    return render_template('model-detection.html', model_loaded=MODEL_LOADED)

@app.route('/rule-detection.html')
def rule_detection():
    return render_template('rule-detection.html')

@app.route('/history.html')
def history():
    return render_template('history.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

# ===== API ENDPOINTS =====
@app.route('/api/analyze/model', methods=['POST'])
def analyze_model():
    """API untuk analisis dengan model ML"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Teks kosong"}), 400
        if len(text) < 10:
            return jsonify({"error": "Teks terlalu pendek (min 10 karakter)"}), 400
        
        predictions, keyword_results = predict_text(text)
        
        return jsonify({
            "success": True,
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "char_count": len(text),
            "predictions": predictions,
            "keyword_matches": keyword_results,
            "model_used": "ml_model" if MODEL_LOADED else "keyword_only",
            "model_name": "SDG_Final_Pipeline.joblib",
            "model_loaded": MODEL_LOADED
        })
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/rule', methods=['POST'])
def analyze_rule():
    """API untuk analisis berbasis aturan"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Teks kosong"}), 400
        
        text_lower = text.lower()
        matched_sdgs = []
        
        # Keyword mapping untuk rule-based (disempurnakan)
        rule_mapping = {
            "No Poverty": ["poverty", "poor", "inequality", "social protection", "basic income", "income", "vulnerable", "deprived"],
            "Zero Hunger": ["hunger", "food security", "nutrition", "agriculture", "malnutrition", "famine", "starvation", "food"],
            "Good Health and Well-being": ["health", "well-being", "disease", "healthcare", "vaccine", "medical", "hospital", "treatment"],
            "Quality Education": ["education", "school", "learning", "literacy", "teacher", "student", "university", "training"],
            "Gender Equality": ["gender", "women", "equality", "empowerment", "feminism", "female", "women's", "girl"],
            "Clean Water and Sanitation": ["water", "sanitation", "hygiene", "clean water", "wastewater", "drinking water", "water supply"],
            "Affordable and Clean Energy": ["energy", "renewable", "solar", "wind", "electricity", "power", "energy efficiency", "energy access"],
            "Decent Work and Economic Growth": ["work", "employment", "economic", "job", "growth", "employment", "labor", "workforce"],
            "Industry, Innovation and Infrastructure": ["industry", "innovation", "infrastructure", "technology", "research", "manufacturing", "digital", "industrial"],
            "Reduced Inequality": ["inequality", "discrimination", "inclusion", "equality", "social justice", "disparity", "gap", "marginalized"],
            "Sustainable Cities and Communities": ["city", "urban", "community", "sustainable", "housing", "transport", "urban planning", "resilient"],
            "Responsible Consumption and Production": ["consumption", "production", "waste", "recycle", "sustainable", "circular economy", "resource efficiency"],
            "Climate Action": ["climate", "global warming", "carbon", "emission", "environment", "climate change", "greenhouse", "temperature"],
            "Life Below Water": ["ocean", "marine", "sea", "fish", "coral", "marine life", "fisheries", "coastal"],
            "Life on Land": ["forest", "biodiversity", "land", "ecosystem", "wildlife", "deforestation", "conservation", "terrestrial"],
            "Peace, Justice and Strong Institutions": ["peace", "justice", "institution", "law", "corruption", "governance", "human rights", "security"],
            "Partnerships for the Goals": ["partnership", "collaboration", "cooperation", "global", "sustainable", "multilateral", "international"]
        }
        
        for sdg, keywords in rule_mapping.items():
            matches = []
            for keyword in keywords:
                if keyword in text_lower:
                    matches.append(keyword)
            
            if matches:
                confidence = min(100, len(matches) * 15)  # 15% per match
                matched_sdgs.append({
                    "sdg": format_sdg_label(sdg),
                    "matched_rules": matches,
                    "match_count": len(matches),
                    "confidence": confidence,
                    "source": "rule_based"
                })
        
        # Sort by confidence
        matched_sdgs.sort(key=lambda x: x["confidence"], reverse=True)
        
        return jsonify({
            "success": True,
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "total_matches": sum([sdg["match_count"] for sdg in matched_sdgs]),
            "matched_sdgs": matched_sdgs[:5],  # Batasi 5 hasil terbaik
            "model_used": "rule_based"
        })
    
    except Exception as e:
        logger.error(f"Rule analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload/document', methods=['POST'])
def upload_document():
    """API untuk upload dan ekstraksi dokumen"""
    if 'file' not in request.files:
        return jsonify({"error": "Tidak ada file"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "File tidak dipilih"}), 400
    
    try:
        file_bytes = file.read()
        filename = file.filename
        
        # Validasi ukuran file
        if len(file_bytes) > app.config['MAX_CONTENT_LENGTH']:
            return jsonify({"error": "File terlalu besar (max 16MB)"}), 413
        
        # Ekstraksi teks
        extractor = DocumentExtractor()
        text, file_type, success = extractor.extract_from_bytes(file_bytes, filename)
        
        if not success:
            return jsonify({"error": text}), 400
        
        if not text.strip():
            return jsonify({"error": "Teks kosong setelah ekstraksi"}), 400
        
        return jsonify({
            "success": True,
            "filename": filename,
            "file_type": file_type,
            "extracted_text": text,
            "text_preview": text[:500] + "..." if len(text) > 500 else text,
            "char_count": len(text)
        })
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

@app.route('/api/system/health', methods=['GET'])
def health_check():
    """Endpoint untuk cek kesehatan sistem"""
    return jsonify({
        "status": "healthy" if MODEL_LOADED else "degraded",
        "model_loaded": MODEL_LOADED,
        "model": "SDG_Final_Pipeline.joblib",
        "sdg_labels_count": len(SDG_LABELS),
        "api_version": "1.0.0",
        "extractor_available": True
    })

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Endpoint untuk informasi sistem"""
    sdg_display = {f"SDG {i+1}": label for i, label in enumerate(SDG_LABELS)}
    
    return jsonify({
        "model": "SDG_Final_Pipeline.joblib",
        "model_type": "ml_model",
        "model_loaded": MODEL_LOADED,
        "sdg_labels": sdg_display,
        "max_upload_size_mb": app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024),
        "supported_formats": ["pdf", "docx", "doc", "txt", "rtf", "md"],
        "features": {
            "text_analysis": True,
            "document_extraction": True,
            "ml_model_classification": MODEL_LOADED,
            "rule_based_detection": True,
            "keyword_matching": True
        }
    })

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint tidak ditemukan"}), 404
    return render_template('index.html', model_loaded=MODEL_LOADED), 404

@app.errorhandler(413)
def too_large(e):
    return jsonify({"error": "File terlalu besar (max 16MB)"}), 413

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Server error: {str(e)}")
    return jsonify({"error": "Kesalahan server internal"}), 500

# ===== MAIN =====
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("\n" + "="*60)
    print("SDGs DOCUMENT CLASSIFICATION SYSTEM")
    print("="*60)
    print(f"Server running on: http://localhost:{port}")
    print(f"Model loaded: {'✓' if MODEL_LOADED else '✗'}")
    print(f"Debug mode: {debug}")
    print("="*60)
    print("\nAvailable routes:")
    print(f"  • Home: http://localhost:{port}/")
    print(f"  • Model Detection: http://localhost:{port}/model-detection.html")
    print(f"  • Rule Detection: http://localhost:{port}/rule-detection.html")
    print(f"  • History: http://localhost:{port}/history.html")
    print(f"  • About: http://localhost:{port}/about.html")
    print(f"  • API Health: http://localhost:{port}/api/system/health")
    print("="*60)
    
    app.run(host='0.0.0.0', port=port, debug=debug)
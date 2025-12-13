import os
import logging
import warnings
from flask import Flask, request, jsonify, render_template, send_from_directory
from document_extractor import DocumentExtractor
from model_loader import SDGModelLoader
from rule_engine import RuleEngine

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
pytorch_model = None
rule_engine = None
MODEL_LOADED = False
RULES_LOADED = False

# ===== LOAD MODEL & RULES =====
def initialize_system():
    global pytorch_model, rule_engine, MODEL_LOADED, RULES_LOADED
    
    # Load PyTorch model
    try:
        logger.info("Initializing PyTorch model...")
        pytorch_model = SDGModelLoader("models/best_model.pt")
        MODEL_LOADED = pytorch_model.load_model()
        
        if MODEL_LOADED:
            logger.info("✓ PyTorch model loaded successfully!")
        else:
            logger.warning("✗ PyTorch model failed to load - using fallback mode")
    except Exception as e:
        logger.error(f"Error loading PyTorch model: {str(e)}")
        MODEL_LOADED = False
    
    # Load Rule Engine
    try:
        logger.info("Initializing Rule Engine...")
        rule_engine = RuleEngine("models/rules")
        RULES_LOADED = rule_engine.load_rules()
        
        if RULES_LOADED:
            logger.info("✓ Rule engine loaded successfully!")
        else:
            logger.warning("✗ Rule engine failed to load")
    except Exception as e:
        logger.error(f"Error loading Rule Engine: {str(e)}")
        RULES_LOADED = False
    
    return MODEL_LOADED or RULES_LOADED

# Initialize pada startup
initialize_system()

# ===== HELPER FUNCTIONS =====
def format_sdg_label(label: str):
    """Ubah nama SDG menjadi 'SDG X: Nama SDG'"""
    if label in SDG_LABELS:
        idx = SDG_LABELS.index(label) + 1
        return f"SDG {idx}: {label}"
    return label

# ===== ROUTES =====
@app.route('/')
def home():
    return render_template('index.html', 
                           model_loaded=MODEL_LOADED,
                           rules_loaded=RULES_LOADED,
                           model_name="PyTorch SDG Model")

@app.route('/index.html')
def index():
    return home()

@app.route('/model-detection.html')
def model_detection():
    return render_template('model-detection.html', 
                           model_loaded=MODEL_LOADED)

@app.route('/rule-detection.html')
def rule_detection():
    return render_template('rule-detection.html',
                           rules_loaded=RULES_LOADED)

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
    """API untuk analisis dengan PyTorch model"""
    try:
        if not MODEL_LOADED:
            logger.warning("Model not loaded, will use fallback mode")
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Teks kosong"}), 400
        if len(text) < 10:
            return jsonify({"error": "Teks terlalu pendek (min 10 karakter)"}), 400
        
        # Predict dengan PyTorch model
        predictions = pytorch_model.predict(text, threshold=0.05)
        
        if not predictions:
            # Fallback jika tidak ada prediksi
            predictions = [{
                "sdg": format_sdg_label("Partnerships for the Goals"),
                "confidence": 50.0,
                "source": "fallback",
                "note": "No specific SDG detected"
            }]
        
        return jsonify({
            "success": True,
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "char_count": len(text),
            "predictions": predictions,
            "model_used": "pytorch_model" if MODEL_LOADED else "keyword_fallback",
            "model_name": "PyTorch SDG Classifier",
            "model_loaded": MODEL_LOADED
        })
    
    except Exception as e:
        logger.error(f"Prediction error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze/rule', methods=['POST'])
def analyze_rule():
    """API untuk analisis berbasis aturan JSON"""
    try:
        if not RULES_LOADED:
            return jsonify({
                "error": "Rules not loaded. Please check server logs.",
                "success": False
            }), 503
        
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Teks kosong"}), 400
        
        # Configuration dari request (optional)
        match_field = data.get('match_field', 'all')
        min_matches = data.get('min_matches', 2)
        
        # Analyze dengan rule engine
        matched_sdgs = rule_engine.analyze(
            text, 
            match_field=match_field,
            min_matches=min_matches
        )
        
        # Calculate total matches
        total_matches = sum([sdg["match_count"] for sdg in matched_sdgs])
        
        return jsonify({
            "success": True,
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "total_matches": total_matches,
            "matched_sdgs": matched_sdgs[:10],
            "model_used": "rule_based",
            "rules_loaded": RULES_LOADED,
            "match_field": match_field
        })
    
    except Exception as e:
        logger.error(f"Rule analysis error: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload/document', methods=['POST'])
def upload_document():
    """
    API untuk upload dan ekstraksi dokumen dengan struktur
    
    Returns structured data: title, abstract, keywords, full_text
    """
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
        
        # Ekstraksi dengan struktur
        extractor = DocumentExtractor()
        structured, file_type, success = extractor.extract_structured(file_bytes, filename)
        
        if not success:
            # Fallback ke ekstraksi biasa
            text, file_type, success = extractor.extract_from_bytes(file_bytes, filename)
            if not success:
                return jsonify({"error": text}), 400
            
            # Return simple structure
            structured = {
                "title": "Untitled Document",
                "abstract": text[:500] if len(text) > 500 else text,
                "keywords": [],
                "full_text": text,
                "authors": [],
                "year": ""
            }
        
        if not structured["full_text"].strip():
            return jsonify({"error": "Teks kosong setelah ekstraksi"}), 400
        
        # Prepare response
        response = {
            "success": True,
            "filename": filename,
            "file_type": file_type,
            "extracted_text": structured["full_text"],
            "text_preview": structured["full_text"][:500] + "..." if len(structured["full_text"]) > 500 else structured["full_text"],
            "char_count": len(structured["full_text"]),
            
            # Structured fields
            "title": structured["title"],
            "abstract": structured["abstract"],
            "keywords": structured["keywords"],
            "authors": structured["authors"],
            "year": structured["year"],
            
            # Metadata
            "has_structure": bool(structured["title"] or structured["abstract"] or structured["keywords"]),
            "structure_quality": "high" if (structured["title"] and structured["abstract"] and structured["keywords"]) else 
                                 "medium" if (structured["title"] or structured["abstract"]) else "low"
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        return jsonify({"error": f"Processing error: {str(e)}"}), 500

@app.route('/api/system/health', methods=['GET'])
def health_check():
    """Endpoint untuk cek kesehatan sistem"""
    return jsonify({
        "status": "healthy" if (MODEL_LOADED or RULES_LOADED) else "degraded",
        "model_loaded": MODEL_LOADED,
        "rules_loaded": RULES_LOADED,
        "pytorch_model": "PyTorch SDG Classifier",
        "sdg_labels_count": len(SDG_LABELS),
        "api_version": "2.0.0",
        "extractor_available": True,
        "structured_extraction": True
    })

@app.route('/api/system/info', methods=['GET'])
def system_info():
    """Endpoint untuk informasi sistem"""
    sdg_display = {f"SDG {i+1}": label for i, label in enumerate(SDG_LABELS)}
    
    info = {
        "pytorch_model": "PyTorch SDG Classifier",
        "model_type": "pytorch",
        "model_loaded": MODEL_LOADED,
        "rules_loaded": RULES_LOADED,
        "sdg_labels": sdg_display,
        "max_upload_size_mb": app.config['MAX_CONTENT_LENGTH'] / (1024 * 1024),
        "supported_formats": ["pdf", "docx", "doc", "txt", "rtf", "md"],
        "features": {
            "text_analysis": True,
            "document_extraction": True,
            "structured_extraction": True,
            "pytorch_classification": MODEL_LOADED,
            "rule_based_detection": RULES_LOADED,
            "keyword_matching": RULES_LOADED,
            "title_detection": True,
            "abstract_detection": True,
            "keyword_detection": True
        }
    }
    
    # Add model info
    if MODEL_LOADED and pytorch_model:
        info["pytorch_model_info"] = pytorch_model.get_model_info()
    
    # Add rules info
    if RULES_LOADED and rule_engine:
        info["rules_summary"] = rule_engine.get_rules_summary()
    
    return jsonify(info)

@app.route('/api/rules/preview', methods=['GET'])
def rules_preview():
    """Endpoint untuk preview rules"""
    if not RULES_LOADED:
        return jsonify({"error": "Rules not loaded"}), 503
    
    sdg = request.args.get('sdg', type=int)
    
    if sdg and 1 <= sdg <= 17:
        keywords = rule_engine.get_sdg_keywords(sdg)
        return jsonify({
            "sdg": sdg,
            "keywords": keywords
        })
    else:
        return jsonify(rule_engine.get_rules_summary())

# ===== ERROR HANDLERS =====
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith('/api/'):
        return jsonify({"error": "Endpoint tidak ditemukan"}), 404
    return render_template('index.html', 
                           model_loaded=MODEL_LOADED,
                           rules_loaded=RULES_LOADED), 404

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
    print("SDGs DOCUMENT CLASSIFICATION SYSTEM - v2.0")
    print("="*60)
    print(f"Server running on: http://localhost:{port}")
    print(f"PyTorch Model: {'✓ LOADED' if MODEL_LOADED else '✗ NOT LOADED (using fallback)'}")
    print(f"Rule Engine: {'✓ LOADED' if RULES_LOADED else '✗ NOT LOADED'}")
    print(f"Structured Extraction: ✓ ENABLED")
    print(f"Debug mode: {debug}")
    print("="*60)
    print("\nAvailable routes:")
    print(f"  • Home: http://localhost:{port}/")
    print(f"  • Model Detection: http://localhost:{port}/model-detection.html")
    print(f"  • Rule Detection: http://localhost:{port}/rule-detection.html")
    print(f"  • History: http://localhost:{port}/history.html")
    print(f"  • About: http://localhost:{port}/about.html")
    print(f"  • API Health: http://localhost:{port}/api/system/health")
    print(f"  • API Info: http://localhost:{port}/api/system/info")
    print("="*60)
    print("\n✨ New Feature: Structured PDF Extraction")
    print("   - Auto-detect Title")
    print("   - Auto-detect Abstract")
    print("   - Auto-detect Keywords")
    print("   - Auto-detect Authors & Year")
    print("="*60 + "\n")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

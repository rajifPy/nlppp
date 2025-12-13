// CERMAT - Main Application JavaScript
// Global State
let currentModel = "bert-base-uncased";
let isModelReady = false;
let historyData = [];
let sdgRules = {};

// SDG Information
const sdgInfo = {
    1: { title: "No Poverty", color: "#E5243B" },
    2: { title: "Zero Hunger", color: "#DDA63A" },
    3: { title: "Good Health and Well-being", color: "#4C9F38" },
    4: { title: "Quality Education", color: "#C5192D" },
    5: { title: "Gender Equality", color: "#FF3A21" },
    6: { title: "Clean Water and Sanitation", color: "#26BDE2" },
    7: { title: "Affordable and Clean Energy", color: "#FCC30B" },
    8: { title: "Decent Work and Economic Growth", color: "#A21942" },
    9: { title: "Industry, Innovation and Infrastructure", color: "#FD6925" },
    10: { title: "Reduced Inequality", color: "#DD1367" },
    11: { title: "Sustainable Cities and Communities", color: "#FD9D24" },
    12: { title: "Responsible Consumption and Production", color: "#BF8B2E" },
    13: { title: "Climate Action", color: "#3F7E44" },
    14: { title: "Life Below Water", color: "#0A97D9" },
    15: { title: "Life on Land", color: "#56C02B" },
    16: { title: "Peace, Justice and Strong Institutions", color: "#00689D" },
    17: { title: "Partnerships for the Goals", color: "#19486A" }
};

// API Endpoints
const API_BASE = window.location.origin;
const API_ENDPOINTS = {
    MODEL_ANALYZE: '/api/analyze/model',
    RULE_ANALYZE: '/api/analyze/rule',
    UPLOAD_DOCUMENT: '/api/upload/document',
    HEALTH_CHECK: '/api/system/health',
    SYSTEM_INFO: '/api/system/info'
};

// Initialize application based on current page
document.addEventListener('DOMContentLoaded', function () {
    console.log("CERMAT Application Initialized");

    const currentPage = getCurrentPage();

    // Common setup for all pages
    setupCommonEventListeners();
    loadHistoryFromStorage();
    checkBackendHealth();

    // Page-specific initialization
    switch (currentPage) {
        case 'index':
            setupLandingPage();
            break;
        case 'model-detection':
            setupModelDetectionPage();
            break;
        case 'rule-detection':
            setupRuleDetectionPage();
            break;
        case 'history':
            setupHistoryPage();
            break;
        case 'about':
            setupAboutPage();
            break;
    }

    // Setup mobile menu
    setupMobileMenu();
});

// ===== COMMON FUNCTIONS =====
function getCurrentPage() {
    const path = window.location.pathname;
    if (path.includes('model-detection')) return 'model-detection';
    if (path.includes('rule-detection')) return 'rule-detection';
    if (path.includes('history')) return 'history';
    if (path.includes('about')) return 'about';
    return 'index';
}

async function checkBackendHealth() {
    try {
        const response = await fetch(API_ENDPOINTS.HEALTH_CHECK);
        const data = await response.json();
        isModelReady = data.model_loaded;

        // Update status indicator if exists
        const indicator = document.getElementById('model-status-indicator');
        const text = document.getElementById('model-status-text');
        if (indicator && text) {
            if (isModelReady) {
                indicator.style.background = '#4CAF50';
                indicator.style.animation = 'none';
                text.textContent = 'Model Ready';
                text.style.color = '#4CAF50';
            } else {
                indicator.style.background = '#f44336';
                text.textContent = 'Model Not Loaded';
                text.style.color = '#f44336';
            }
        }

        return data.model_loaded;
    } catch (error) {
        console.error('Backend health check failed:', error);
        isModelReady = false;
        return false;
    }
}

function setupCommonEventListeners() {
    // Setup tab switching for option tabs
    document.querySelectorAll('.option-tab').forEach(tab => {
        tab.addEventListener('click', function () {
            const option = this.dataset.option;
            switchOption(option);
        });
    });

    // Character count for textareas
    document.querySelectorAll('textarea').forEach(textarea => {
        textarea.addEventListener('input', function () {
            updateCharCount(this);
        });
    });

    // Range slider updates
    document.querySelectorAll('input[type="range"]').forEach(slider => {
        slider.addEventListener('input', function () {
            const valueSpan = document.getElementById(this.id + '-value');
            if (valueSpan) {
                valueSpan.textContent = this.value;
            }
        });
    });
}

function setupMobileMenu() {
    const toggleBtn = document.querySelector('.nav-mobile-toggle');
    const navMenu = document.querySelector('.nav-menu');

    if (toggleBtn && navMenu) {
        toggleBtn.addEventListener('click', function () {
            navMenu.classList.toggle('active');
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!navMenu.contains(e.target) && !toggleBtn.contains(e.target)) {
                navMenu.classList.remove('active');
            }
        });
    }
}

function switchOption(option) {
    // Update tab buttons
    document.querySelectorAll('.option-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.option === option);
    });

    // Update content
    document.querySelectorAll('.option-content').forEach(content => {
        content.classList.toggle('active', content.id === option + '-option');
    });
}

function updateCharCount(textarea) {
    const charCount = textarea.value.length;
    const countElement = document.getElementById(textarea.id + '-char-count');
    if (countElement) {
        countElement.textContent = charCount;
    }
}

// ===== LANDING PAGE FUNCTIONS =====
function setupLandingPage() {
    loadSDGPreview();
}

function loadSDGPreview() {
    const container = document.getElementById('sdg-preview');
    if (!container) return;

    let html = '';
    for (let i = 1; i <= 17; i++) {
        html += `
            <div class="sdg-card" data-sdg="${i}">
                <div class="sdg-image">
                    <img src="/static/images/sdg${i}.png" alt="SDG ${i}" onerror="this.src='/static/images/sdg.png'">
                </div>
                <div class="sdg-number">SDG ${i}</div>
                <div class="sdg-title">${sdgInfo[i].title}</div>
            </div>
        `;
    }
    container.innerHTML = html;

    // Add click events
    document.querySelectorAll('.sdg-card').forEach(card => {
        card.addEventListener('click', function () {
            const sdg = this.dataset.sdg;
            showSDGModal(sdg);
        });
    });
}

function showSDGModal(sdgNumber) {
    const sdg = sdgInfo[sdgNumber];
    const modal = createModal(`
        <div class="sdg-modal-content">
            <div class="sdg-modal-header" style="background: ${sdg.color}">
                <h3>SDG ${sdgNumber}: ${sdg.title}</h3>
            </div>
            <div class="sdg-modal-body">
                <div class="sdg-image-large">
                    <img src="/static/images/sdg${sdgNumber}.png" alt="SDG ${sdgNumber}" 
                         onerror="this.src='/static/images/sdg.png'">
                </div>
                <div class="sdg-description">
                    <h4>About this Goal</h4>
                    <p>This Sustainable Development Goal focuses on...</p>
                    <div class="sdg-keywords">
                        <h5>Common Keywords:</h5>
                        <div class="keyword-tags">
                            <span class="keyword-tag">keyword1</span>
                            <span class="keyword-tag">keyword2</span>
                            <span class="keyword-tag">keyword3</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `);

    modal.classList.add('active');
}

// ===== MODEL DETECTION PAGE FUNCTIONS =====
function setupModelDetectionPage() {
    checkBackendHealth();
    setupFileUpload();
    setupAnalyzeButton();
}

function setupFileUpload() {
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
        fileInput.addEventListener('change', handleFileUpload);
    }
}

// ===== ENHANCED FILE UPLOAD HANDLER WITH STRUCTURED EXTRACTION =====

async function handleFileUpload(e) {
    const file = e.target.files[0];
    const fileInfo = document.getElementById('file-info');

    if (!file) return;

    if (file.size > 16 * 1024 * 1024) {
        showNotification('File too large (max 16MB)', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showLoading(fileInfo, 'Uploading and extracting document structure...');

    try {
        const response = await fetch(API_ENDPOINTS.UPLOAD_DOCUMENT, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            // Display structured information
            let structureHtml = '';

            // Show structure quality indicator
            const qualityIcons = {
                'high': '<i class="fas fa-star" style="color: #4CAF50;"></i>',
                'medium': '<i class="fas fa-star-half-alt" style="color: #FF9800;"></i>',
                'low': '<i class="far fa-star" style="color: #999;"></i>'
            };

            const qualityIcon = qualityIcons[data.structure_quality] || '';

            structureHtml = `
                <div class="file-info-loaded">
                    <i class="fas fa-file-alt" style="color: #0189BB; font-size: 2.5rem;"></i>
                    <div class="file-details" style="flex: 1;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <h4>${data.filename}</h4>
                            <span class="structure-badge" title="Structure Detection Quality">
                                ${qualityIcon} ${data.structure_quality.toUpperCase()}
                            </span>
                        </div>
                        <p>${data.file_type} • ${data.char_count.toLocaleString()} characters</p>
                        
                        ${data.has_structure ? `
                            <div class="extracted-structure" style="margin-top: 15px; padding: 15px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #0189BB;">
                                
                                ${data.title ? `
                                    <div class="structure-field" style="margin-bottom: 10px;">
                                        <strong style="color: #014576;">
                                            <i class="fas fa-heading"></i> Title:
                                        </strong>
                                        <p style="margin: 5px 0; color: #333;">${data.title}</p>
                                    </div>
                                ` : ''}
                                
                                ${data.abstract ? `
                                    <div class="structure-field" style="margin-bottom: 10px;">
                                        <strong style="color: #014576;">
                                            <i class="fas fa-align-left"></i> Abstract:
                                        </strong>
                                        <p style="margin: 5px 0; color: #555; font-size: 0.9rem;">
                                            ${data.abstract.substring(0, 200)}${data.abstract.length > 200 ? '...' : ''}
                                        </p>
                                    </div>
                                ` : ''}
                                
                                ${data.keywords && data.keywords.length > 0 ? `
                                    <div class="structure-field" style="margin-bottom: 10px;">
                                        <strong style="color: #014576;">
                                            <i class="fas fa-tags"></i> Keywords (${data.keywords.length}):
                                        </strong>
                                        <div style="display: flex; flex-wrap: wrap; gap: 5px; margin-top: 5px;">
                                            ${data.keywords.slice(0, 8).map(kw =>
                `<span style="background: #0189BB; color: white; padding: 3px 10px; border-radius: 12px; font-size: 0.85rem;">${kw}</span>`
            ).join('')}
                                            ${data.keywords.length > 8 ? `<span style="color: #666; font-size: 0.85rem;">+${data.keywords.length - 8} more</span>` : ''}
                                        </div>
                                    </div>
                                ` : ''}
                                
                                ${data.authors && data.authors.length > 0 ? `
                                    <div class="structure-field" style="margin-bottom: 5px;">
                                        <strong style="color: #014576;">
                                            <i class="fas fa-user"></i> Authors:
                                        </strong>
                                        <span style="color: #555; font-size: 0.9rem;">
                                            ${data.authors.slice(0, 3).join(', ')}${data.authors.length > 3 ? ' et al.' : ''}
                                        </span>
                                    </div>
                                ` : ''}
                                
                                ${data.year ? `
                                    <div class="structure-field">
                                        <strong style="color: #014576;">
                                            <i class="fas fa-calendar"></i> Year:
                                        </strong>
                                        <span style="color: #555; font-size: 0.9rem;">${data.year}</span>
                                    </div>
                                ` : ''}
                            </div>
                        ` : `
                            <p style="margin-top: 10px; color: #999; font-size: 0.9rem;">
                                <i class="fas fa-info-circle"></i> No structured data detected. Using full text for analysis.
                            </p>
                        `}
                        
                        <p class="upload-status" style="margin-top: 10px;">
                            <i class="fas fa-check-circle" style="color: #4CAF50;"></i> Ready for analysis
                        </p>
                        
                        <button onclick="autoFillFields('${data.title?.replace(/'/g, "\\'")}', '${data.abstract?.replace(/'/g, "\\'")}', '${data.keywords?.join(', ').replace(/'/g, "\\'")}')" 
                                class="icon-btn" 
                                style="margin-top: 10px; font-size: 0.85rem;">
                            <i class="fas fa-magic"></i> Auto-fill Form Fields
                        </button>
                    </div>
                </div>
            `;

            fileInfo.innerHTML = structureHtml;

            // Store extracted data
            localStorage.setItem('current_document_text', data.extracted_text);
            localStorage.setItem('current_document_structure', JSON.stringify({
                title: data.title,
                abstract: data.abstract,
                keywords: data.keywords,
                authors: data.authors,
                year: data.year
            }));

            showNotification('Document analyzed successfully! Structure detected.', 'success');
        } else {
            showNotification(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Upload failed. Please try again.', 'error');
    }
}

// Auto-fill form fields with extracted data
function autoFillFields(title, abstract, keywords) {
    // Decode HTML entities
    const decode = (str) => {
        const txt = document.createElement('textarea');
        txt.innerHTML = str;
        return txt.value;
    };

    // Fill title
    const titleInput = document.getElementById('title-input');
    if (titleInput && title) {
        titleInput.value = decode(title);
    }

    // Fill abstract
    const abstractInput = document.getElementById('abstract-input');
    if (abstractInput && abstract) {
        abstractInput.value = decode(abstract);
        updateCharCount(abstractInput);
    }

    // Fill keywords
    const keywordsInput = document.getElementById('keywords-input');
    if (keywordsInput && keywords) {
        keywordsInput.value = decode(keywords);
    }

    // Switch to manual input tab
    switchOption('manual');

    showNotification('Form fields auto-filled!', 'success');
}

// Add CSS for structure badge
const style = document.createElement('style');
style.textContent = `
    .structure-badge {
        background: rgba(1, 137, 187, 0.1);
        padding: 4px 10px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        color: #014576;
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
    
    .extracted-structure {
        animation: slideIn 0.3s ease;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(-10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .structure-field strong {
        display: inline-flex;
        align-items: center;
        gap: 5px;
    }
`;
document.head.appendChild(style);

function setupAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyze-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeWithModel);
    }
}

async function analyzeWithModel() {
    if (!isModelReady) {
        showNotification('Model is not ready. Please check backend.', 'warning');
        return;
    }

    const resultsContainer = document.getElementById('results-container');
    const saveBtn = document.getElementById('save-btn');

    // Get text from manual input or uploaded file
    let text = '';
    const manualText = document.getElementById('abstract-input')?.value;
    const uploadedText = localStorage.getItem('current_document_text');

    if (manualText && manualText.trim().length > 0) {
        text = manualText;
    } else if (uploadedText) {
        text = uploadedText;
    } else {
        showNotification('Please upload a document or enter text to analyze', 'warning');
        return;
    }

    // Show loading
    showLoading(resultsContainer, 'Analyzing document with AI model...');

    try {
        const response = await fetch(API_ENDPOINTS.MODEL_ANALYZE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (data.success) {
            displayModelResults(data);

            // Enable save button
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.onclick = () => saveModelResults(data);
            }

            showNotification('Analysis complete!', 'success');
        } else {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Analysis Failed</h3>
                    <p>${data.error || 'Unknown error'}</p>
                </div>
            `;
            showNotification('Analysis failed', 'error');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Network Error</h3>
                <p>Failed to connect to backend server</p>
            </div>
        `;
        showNotification('Network error. Please check server connection.', 'error');
    }
}

function displayModelResults(data) {
    const container = document.getElementById('results-container');
    const detailedContainer = document.getElementById('detailed-results');

    if (!data.predictions || data.predictions.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <h3>No Predictions Found</h3>
                <p>The document could not be classified</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="results-header">
            <h3>AI Classification Results</h3>
            <p class="results-subtitle">${new Date().toLocaleString()}</p>
            <p class="results-meta">Model: ${data.model_name || 'SDG Model'}</p>
        </div>
        
        <div class="top-predictions">
            <h4><i class="fas fa-trophy"></i> Top Predictions</h4>
            <div class="predictions-grid">
    `;

    data.predictions.forEach((pred, index) => {
        const confidenceClass = pred.confidence > 80 ? 'high' : pred.confidence > 60 ? 'medium' : 'low';
        const medal = index === 0 ? '🥇' : index === 1 ? '🥈' : index === 2 ? '🥉' : '📊';
        const sdgNumber = pred.sdg.split(':')[0].replace('SDG ', '').trim();

        html += `
            <div class="prediction-card">
                <div class="prediction-rank">${medal}</div>
                <div class="prediction-image">
                    <img src="/static/images/sdg${sdgNumber}.png" alt="${pred.sdg}" 
                         onerror="this.src='/static/images/sdg.png'">
                </div>
                <div class="prediction-content">
                    <h5>${pred.sdg}</h5>
                    <div class="confidence-score ${confidenceClass}">
                        <span>${pred.confidence.toFixed(1)}%</span>
                    </div>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${pred.confidence}%"></div>
                    </div>
                    <p class="prediction-source">Source: ${pred.source}</p>
                </div>
            </div>
        `;
    });

    html += `
            </div>
        </div>
    `;

    if (data.keyword_matches && data.keyword_matches.length > 0) {
        html += `
            <div class="keyword-matches">
                <h4><i class="fas fa-key"></i> Keyword Matches</h4>
                <div class="keyword-tags">
                    ${data.keyword_matches.map(keyword => `<span class="keyword-tag">${keyword}</span>`).join('')}
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
    if (detailedContainer) detailedContainer.style.display = 'block';
}

function saveModelResults(data) {
    const historyEntry = {
        id: Date.now(),
        type: 'model',
        title: document.getElementById('title-input')?.value || "Untitled Document",
        abstract: document.getElementById('abstract-input')?.value || data.text_preview || "",
        keywords: document.getElementById('keywords-input')?.value || "",
        results: data.predictions,
        model_used: data.model_used,
        timestamp: new Date().toISOString()
    };

    historyData.push(historyEntry);
    saveHistoryToStorage();
    showNotification('Results saved to history', 'success');
}

// ===== RULE DETECTION PAGE FUNCTIONS =====
function setupRuleDetectionPage() {
    loadRules();
    setupRuleFileUpload();
    setupRuleAnalyzeButton();
    loadRulesPreview();
}

function loadRules() {
    sdgRules = {
        1: ["poverty", "poor", "inequality", "social protection", "basic income"],
        2: ["hunger", "food security", "nutrition", "agriculture", "malnutrition"],
        3: ["health", "well-being", "disease", "healthcare", "vaccine"],
        4: ["education", "school", "learning", "literacy", "teacher"],
        5: ["gender", "women", "equality", "empowerment", "feminism"],
        6: ["water", "sanitation", "hygiene", "clean water", "wastewater"],
        7: ["energy", "renewable", "solar", "wind", "electricity"],
        8: ["work", "employment", "economic", "job", "growth"],
        9: ["industry", "innovation", "infrastructure", "technology", "research"],
        10: ["inequality", "discrimination", "inclusion", "equality", "social justice"],
        11: ["city", "urban", "community", "sustainable", "housing"],
        12: ["consumption", "production", "waste", "recycle", "sustainable"],
        13: ["climate", "global warming", "carbon", "emission", "environment"],
        14: ["ocean", "marine", "sea", "fish", "coral"],
        15: ["forest", "biodiversity", "land", "ecosystem", "wildlife"],
        16: ["peace", "justice", "institution", "law", "corruption"],
        17: ["partnership", "collaboration", "cooperation", "global", "sustainable"]
    };

    const rulesCount = Object.values(sdgRules).reduce((sum, rules) => sum + rules.length, 0);
    const countElement = document.getElementById('rules-count');
    if (countElement) {
        countElement.textContent = rulesCount;
    }
}

function setupRuleFileUpload() {
    const fileInput = document.getElementById('file-input-rule');
    if (fileInput) {
        fileInput.addEventListener('change', handleRuleFileUpload);
    }
}

async function handleRuleFileUpload(e) {
    const file = e.target.files[0];
    const fileInfo = document.getElementById('file-info-rule');

    if (!file) return;

    if (file.size > 16 * 1024 * 1024) {
        showNotification('File too large (max 16MB)', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    showLoading(fileInfo, 'Uploading and extracting text...');

    try {
        const response = await fetch(API_ENDPOINTS.UPLOAD_DOCUMENT, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            fileInfo.innerHTML = `
                <div class="file-info-loaded">
                    <i class="fas fa-file-alt" style="color: #0189BB;"></i>
                    <div class="file-details">
                        <h4>${data.filename}</h4>
                        <p>${data.file_type} • ${data.char_count} characters</p>
                        <p class="upload-status">
                            <i class="fas fa-check-circle" style="color: #4CAF50;"></i> Ready for rule matching
                        </p>
                    </div>
                </div>
            `;

            // Store extracted text for analysis
            localStorage.setItem('current_document_text_rule', data.extracted_text);
            showNotification('Document uploaded successfully', 'success');
        } else {
            showNotification(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Upload failed. Please try again.', 'error');
    }
}

function setupRuleAnalyzeButton() {
    const analyzeBtn = document.getElementById('analyze-rule-btn');
    if (analyzeBtn) {
        analyzeBtn.addEventListener('click', analyzeWithRules);
    }
}

async function analyzeWithRules() {
    const resultsContainer = document.getElementById('results-container-rule');
    const saveBtn = document.getElementById('save-rule-btn');

    // Get text from manual input or uploaded file
    let text = '';
    const manualText = document.getElementById('abstract-input-rule')?.value;
    const uploadedText = localStorage.getItem('current_document_text_rule');

    if (manualText && manualText.trim().length > 0) {
        text = manualText;
    } else if (uploadedText) {
        text = uploadedText;
    } else {
        showNotification('Please upload a document or enter text to analyze', 'warning');
        return;
    }

    // Show loading
    showLoading(resultsContainer, 'Analyzing with rule-based detection...');

    try {
        const response = await fetch(API_ENDPOINTS.RULE_ANALYZE, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });

        const data = await response.json();

        if (data.success) {
            displayRuleResults(data);

            // Enable save button
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.onclick = () => saveRuleResults(data);
            }

            showNotification('Rule matching complete!', 'success');
        } else {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h3>Analysis Failed</h3>
                    <p>${data.error || 'Unknown error'}</p>
                </div>
            `;
            showNotification('Analysis failed', 'error');
        }
    } catch (error) {
        console.error('Analysis error:', error);
        resultsContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-exclamation-triangle"></i>
                <h3>Network Error</h3>
                <p>Failed to connect to backend server</p>
            </div>
        `;
        showNotification('Network error. Please check server connection.', 'error');
    }
}

function displayRuleResults(data) {
    const container = document.getElementById('results-container-rule');
    const detailedContainer = document.getElementById('detailed-rule-results');

    if (!data.matched_sdgs || data.matched_sdgs.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-search"></i>
                <h3>No Rule Matches Found</h3>
                <p>The document did not match any SDG rules.</p>
                <p class="empty-subtext">Try adding more specific keywords or check the rules preview.</p>
            </div>
        `;
        return;
    }

    let html = `
        <div class="results-header">
            <h3>Rule Matching Results</h3>
            <p class="results-subtitle">
                ${data.total_matches} rules matched across ${data.matched_sdgs.length} SDGs
            </p>
        </div>
        
        <div class="rule-matches">
    `;

    data.matched_sdgs.forEach((sdg, index) => {
        const sdgNumber = sdg.sdg.split(':')[0].replace('SDG ', '').trim();

        html += `
            <div class="rule-match-card">
                <div class="match-header">
                    <div class="match-sdg">
                        <div class="sdg-image-small">
                            <img src="/static/images/sdg${sdgNumber}.png" alt="${sdg.sdg}"
                                 onerror="this.src='/static/images/sdg.png'">
                        </div>
                        <h5>${sdg.sdg}</h5>
                    </div>
                    <div class="match-stats">
                        <span class="match-count">${sdg.match_count} rules</span>
                        <span class="confidence-score">${sdg.confidence}%</span>
                    </div>
                </div>
                
                <div class="matched-rules">
                    <h6>Matched Rules:</h6>
                    <div class="rule-tags">
                        ${sdg.matched_rules.map(rule => `<span class="rule-tag">${rule}</span>`).join('')}
                    </div>
                </div>
            </div>
        `;
    });

    html += `</div>`;

    container.innerHTML = html;
    if (detailedContainer) detailedContainer.style.display = 'block';
}

function saveRuleResults(data) {
    const historyEntry = {
        id: Date.now(),
        type: 'rule',
        title: document.getElementById('title-input-rule')?.value || "Untitled Document",
        abstract: document.getElementById('abstract-input-rule')?.value || data.text_preview || "",
        keywords: document.getElementById('keywords-input-rule')?.value || "",
        results: data.matched_sdgs,
        matchedRules: data.matched_sdgs.flatMap(sdg => sdg.matched_rules),
        total_matches: data.total_matches,
        timestamp: new Date().toISOString()
    };

    historyData.push(historyEntry);
    saveHistoryToStorage();
    showNotification('Rule results saved to history', 'success');
}

function loadRulesPreview() {
    const container = document.getElementById('rules-preview-grid');
    if (!container) return;

    let html = '';
    for (let i = 1; i <= 5; i++) {
        const rules = sdgRules[i] || [];
        html += `
            <div class="rules-sdg-preview">
                <div class="preview-header">
                    <div class="sdg-image-tiny">
                        <img src="/static/images/sdg${i}.png" alt="SDG ${i}"
                             onerror="this.src='/static/images/sdg.png'">
                    </div>
                    <h5>SDG ${i}</h5>
                    <span class="rule-count">${rules.length} rules</span>
                </div>
                <div class="preview-rules">
                    ${rules.slice(0, 3).map(rule => `<span class="preview-rule">${rule}</span>`).join('')}
                    ${rules.length > 3 ? '<span class="more-rules">+ more</span>' : ''}
                </div>
            </div>
        `;
    }

    container.innerHTML = html;
}

// ===== HISTORY PAGE FUNCTIONS =====
function setupHistoryPage() {
    loadHistory();
    setupHistoryFilters();
}

function loadHistory() {
    const tableBody = document.getElementById('history-table-body');
    const emptyState = document.getElementById('table-empty');
    const totalEl = document.getElementById('total-classifications');
    const modelEl = document.getElementById('model-classifications');
    const ruleEl = document.getElementById('rule-classifications');

    const modelCount = historyData.filter(item => item.type === 'model').length;
    const ruleCount = historyData.filter(item => item.type === 'rule').length;

    if (totalEl) totalEl.textContent = historyData.length;
    if (modelEl) modelEl.textContent = modelCount;
    if (ruleEl) ruleEl.textContent = ruleCount;

    if (historyData.length === 0) {
        if (tableBody) tableBody.innerHTML = '';
        if (emptyState) emptyState.style.display = 'block';
        return;
    }

    if (emptyState) emptyState.style.display = 'none';

    let html = '';
    historyData.slice(0, 10).forEach(entry => {
        const sdgs = entry.results ? entry.results.map(r => r.sdg.split(':')[0]).join(', ') : 'None';
        const method = entry.type === 'model' ? 'AI Model' : 'Rule-Based';
        const date = new Date(entry.timestamp).toLocaleDateString();

        html += `
            <tr data-id="${entry.id}">
                <td><input type="checkbox" class="history-checkbox" data-id="${entry.id}"></td>
                <td>${entry.title.substring(0, 50)}${entry.title.length > 50 ? '...' : ''}</td>
                <td><span class="method-badge ${entry.type}">${method}</span></td>
                <td>${sdgs}</td>
                <td>${date}</td>
                <td>
                    <button class="action-btn view-btn" onclick="viewHistoryDetail(${entry.id})">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="action-btn delete-btn" onclick="deleteHistoryEntry(${entry.id})">
                        <i class="fas fa-trash-alt"></i>
                    </button>
                </td>
            </tr>
        `;
    });

    if (tableBody) tableBody.innerHTML = html;
    updateBulkActions();
}

function setupHistoryFilters() {
    const searchBox = document.getElementById('history-search');
    const filterMethod = document.getElementById('filter-method');
    const filterSDG = document.getElementById('filter-sdg');
    const filterDate = document.getElementById('filter-date');

    [searchBox, filterMethod, filterSDG, filterDate].forEach(element => {
        if (element) {
            element.addEventListener('change', filterHistory);
        }
    });
}

function filterHistory() {
    loadHistory();
}

function viewHistoryDetail(id) {
    const entry = historyData.find(item => item.id === id);
    if (!entry) return;

    let resultsHtml = '';
    if (entry.type === 'model') {
        resultsHtml = displayModelResultsDetail(entry.results);
    } else {
        resultsHtml = displayRuleResultsDetail(entry.results);
    }

    const modalContent = `
        <div class="history-detail">
            <h4>${entry.title}</h4>
            <p class="detail-meta">
                <span class="detail-method ${entry.type}">${entry.type === 'model' ? 'AI Model' : 'Rule-Based'}</span>
                <span class="detail-date">${new Date(entry.timestamp).toLocaleString()}</span>
            </p>
            
            <div class="detail-section">
                <h5><i class="fas fa-file-alt"></i> Abstract</h5>
                <p>${entry.abstract || 'No abstract provided'}</p>
            </div>
            
            <div class="detail-section">
                <h5><i class="fas fa-tags"></i> Keywords</h5>
                <p>${entry.keywords || 'No keywords provided'}</p>
            </div>
            
            <div class="detail-section">
                <h5><i class="fas fa-chart-bar"></i> Classification Results</h5>
                ${resultsHtml}
            </div>
        </div>
    `;

    const modal = createModal(modalContent);
    modal.classList.add('active');
}

function displayModelResultsDetail(results) {
    if (!results || results.length === 0) return '<p>No classification results</p>';

    let html = '<div class="model-results-detail">';
    results.forEach(pred => {
        html += `
            <div class="prediction-detail">
                <div class="prediction-title">${pred.sdg}</div>
                <div class="prediction-confidence">${pred.confidence.toFixed(1)}% confidence</div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function displayRuleResultsDetail(results) {
    if (!results || results.length === 0) return '<p>No rule matches found</p>';

    let html = '<div class="rule-results-detail">';
    results.forEach(sdg => {
        html += `
            <div class="rule-match-detail">
                <div class="rule-sdg">${sdg.sdg}</div>
                <div class="rule-matched">
                    <strong>${sdg.match_count} rules matched:</strong> ${sdg.matched_rules?.join(', ') || 'No rules'}
                </div>
            </div>
        `;
    });
    html += '</div>';
    return html;
}

function deleteHistoryEntry(id) {
    if (confirm('Are you sure you want to delete this history entry?')) {
        historyData = historyData.filter(item => item.id !== id);
        saveHistoryToStorage();
        loadHistory();
        showNotification('History entry deleted', 'success');
    }
}

function updateBulkActions() {
    const selectedCount = document.querySelectorAll('.history-checkbox:checked').length;
    const bulkActions = document.getElementById('bulk-actions');
    const selectedCountSpan = document.getElementById('selected-count');

    if (bulkActions && selectedCountSpan) {
        if (selectedCount > 0) {
            bulkActions.style.display = 'block';
            selectedCountSpan.textContent = selectedCount;
        } else {
            bulkActions.style.display = 'none';
        }
    }
}

function deleteSelected() {
    const checkboxes = document.querySelectorAll('.history-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.id));

    if (ids.length === 0) {
        showNotification('No items selected', 'warning');
        return;
    }

    if (confirm(`Delete ${ids.length} selected items?`)) {
        historyData = historyData.filter(item => !ids.includes(item.id));
        saveHistoryToStorage();
        loadHistory();
        showNotification(`${ids.length} items deleted`, 'success');
    }
}

// ===== STORAGE FUNCTIONS =====
function loadHistoryFromStorage() {
    const saved = localStorage.getItem('cermat_history');
    if (saved) {
        try {
            historyData = JSON.parse(saved);
        } catch (e) {
            console.error('Error loading history:', e);
            historyData = [];
        }
    }
}

function saveHistoryToStorage() {
    try {
        localStorage.setItem('cermat_history', JSON.stringify(historyData));
    } catch (e) {
        console.error('Error saving history:', e);
    }
}

// ===== UTILITY FUNCTIONS =====
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelector('.notification');
    if (existing) existing.remove();

    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : type === 'warning' ? 'exclamation-triangle' : 'info-circle'}"></i>
        <span>${message}</span>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.style.animation = 'slideOutRight 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }
    }, 5000);
}

function showLoading(container, message = 'Loading...') {
    if (!container) return;

    container.innerHTML = `
        <div class="loading-state">
            <div class="loading-spinner"></div>
            <h4>${message}</h4>
            <p>Please wait while we process your request</p>
        </div>
    `;
}

function createModal(content) {
    // Remove existing modal
    const existing = document.getElementById('custom-modal');
    if (existing) existing.remove();

    const modal = document.createElement('div');
    modal.id = 'custom-modal';
    modal.className = 'modal';
    modal.innerHTML = `
        <div class="modal-content">
            <div class="modal-header">
                <button class="modal-close" onclick="this.closest('.modal').classList.remove('active')">&times;</button>
            </div>
            <div class="modal-body">
                ${content}
            </div>
        </div>
    `;

    document.body.appendChild(modal);

    // Close on background click
    modal.addEventListener('click', function (e) {
        if (e.target === this) {
            this.classList.remove('active');
        }
    });

    // Close on Escape key
    const closeModalOnEscape = function (e) {
        if (e.key === 'Escape') {
            modal.classList.remove('active');
            document.removeEventListener('keydown', closeModalOnEscape);
        }
    };
    document.addEventListener('keydown', closeModalOnEscape);

    return modal;
}

// ===== EXPORT FUNCTIONS =====
function exportResults() {
    const page = getCurrentPage();
    let data = {};
    let filename = 'cermat-';

    if (page === 'model-detection') {
        // Export model results
        data = { type: 'model_results', timestamp: new Date().toISOString() };
        filename += 'model-results-';
    } else if (page === 'rule-detection') {
        // Export rule results
        data = { type: 'rule_results', timestamp: new Date().toISOString() };
        filename += 'rule-results-';
    } else if (page === 'history') {
        // Export selected history
        data = { type: 'history', entries: historyData, timestamp: new Date().toISOString() };
        filename += 'history-';
    }

    filename += new Date().toISOString().replace(/[:.]/g, '-');

    const dataStr = JSON.stringify(data, null, 2);
    const dataUri = 'data:application/json;charset=utf-8,' + encodeURIComponent(dataStr);

    const link = document.createElement('a');
    link.setAttribute('href', dataUri);
    link.setAttribute('download', filename + '.json');
    link.click();

    showNotification('Data exported successfully', 'success');
}

// ===== CLEAR FUNCTIONS =====
function clearResults() {
    const page = getCurrentPage();

    if (page === 'model-detection') {
        const resultsContainer = document.getElementById('results-container');
        const detailedContainer = document.getElementById('detailed-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-robot"></i>
                    <p>Upload a document or enter details above to see AI classification results</p>
                </div>
            `;
        }
        if (detailedContainer) detailedContainer.style.display = 'none';

        // Clear saved text
        localStorage.removeItem('current_document_text');
    } else if (page === 'rule-detection') {
        const resultsContainer = document.getElementById('results-container-rule');
        const detailedContainer = document.getElementById('detailed-rule-results');
        if (resultsContainer) {
            resultsContainer.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-ruler-combined"></i>
                    <p>Upload a document or enter details above to see rule matching results</p>
                </div>
            `;
        }
        if (detailedContainer) detailedContainer.style.display = 'none';

        // Clear saved text
        localStorage.removeItem('current_document_text_rule');
    }

    showNotification('Results cleared', 'info');
}

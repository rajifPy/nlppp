import os
import PyPDF2
import pdfplumber
from docx import Document
import logging
import tempfile
import re
from typing import Tuple, Dict, Optional

logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Ekstrak teks dari berbagai format dokumen dengan deteksi struktur"""
    
    def __init__(self):
        self.supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.md']
    
    @staticmethod
    def extract_from_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, bool]:
        """
        Ekstrak teks dari bytes file
        
        Returns:
            Tuple[text, file_type, success]
        """
        try:
            if not filename or filename.strip() == '':
                return "", "Nama file tidak valid", False
            
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            supported_ext = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.md']
            if ext not in supported_ext:
                return "", f"Format tidak didukung: {ext}", False
            
            # Simpan sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            # Ekstrak berdasarkan ekstensi
            if ext == '.pdf':
                text = DocumentExtractor._extract_pdf(tmp_path)
                file_type = "PDF"
            elif ext == '.docx':
                text = DocumentExtractor._extract_docx(tmp_path)
                file_type = "DOCX"
            elif ext == '.doc':
                text = DocumentExtractor._extract_doc(tmp_path)
                file_type = "DOC"
            elif ext in ['.txt', '.rtf', '.md']:
                text = DocumentExtractor._extract_text(tmp_path)
                file_type = "TEXT"
            else:
                os.unlink(tmp_path)
                return "", f"Format tidak didukung: {ext}", False
            
            # Hapus file temporary
            os.unlink(tmp_path)
            
            if not text or not text.strip():
                return "", "Teks kosong setelah ekstraksi", False
            
            return text, file_type, True
            
        except Exception as e:
            logger.error(f"Extraction error for {filename}: {str(e)}")
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return "", f"Error ekstraksi: {str(e)}", False
    
    @staticmethod
    def extract_structured(file_bytes: bytes, filename: str) -> Tuple[Dict, str, bool]:
        """
        Ekstrak dokumen dengan struktur (Title, Abstract, Keywords)
        
        Returns:
            Tuple[structured_data, file_type, success]
            
        structured_data format:
        {
            "title": str,
            "abstract": str,
            "keywords": list[str],
            "full_text": str,
            "authors": list[str],
            "year": str
        }
        """
        try:
            if not filename or filename.strip() == '':
                return {}, "Nama file tidak valid", False
            
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            if ext not in ['.pdf', '.docx', '.doc', '.txt']:
                return {}, f"Format tidak didukung untuk ekstraksi terstruktur: {ext}", False
            
            # Simpan sementara
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(file_bytes)
                tmp_path = tmp.name
            
            # Ekstrak teks mentah
            if ext == '.pdf':
                full_text = DocumentExtractor._extract_pdf(tmp_path)
                file_type = "PDF"
            elif ext == '.docx':
                full_text = DocumentExtractor._extract_docx(tmp_path)
                file_type = "DOCX"
            elif ext == '.doc':
                full_text = DocumentExtractor._extract_doc(tmp_path)
                file_type = "DOC"
            else:
                full_text = DocumentExtractor._extract_text(tmp_path)
                file_type = "TEXT"
            
            # Hapus file temporary
            os.unlink(tmp_path)
            
            if not full_text or not full_text.strip():
                return {}, "Teks kosong setelah ekstraksi", False
            
            # Parse struktur dari teks
            structured = DocumentExtractor._parse_structure(full_text)
            
            return structured, file_type, True
            
        except Exception as e:
            logger.error(f"Structured extraction error for {filename}: {str(e)}")
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return {}, f"Error ekstraksi: {str(e)}", False
    
    @staticmethod
    def _parse_structure(text: str) -> Dict:
        """
        Parse teks untuk menemukan Title, Abstract, Keywords, dll
        
        Returns:
            Dict with structured data
        """
        lines = text.split('\n')
        
        result = {
            "title": "",
            "abstract": "",
            "keywords": [],
            "full_text": text,
            "authors": [],
            "year": ""
        }
        
        # Clean lines
        lines = [line.strip() for line in lines if line.strip()]
        
        # ===== EXTRACT TITLE =====
        # Title biasanya di baris pertama atau beberapa baris pertama
        # dan biasanya UPPERCASE atau Title Case dengan font besar
        title_candidates = []
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            # Skip jika line terlalu pendek atau terlalu panjang
            if 10 < len(line) < 200:
                # Check if mostly uppercase or title case
                if line.isupper() or line.istitle():
                    title_candidates.append((i, line, len(line)))
        
        if title_candidates:
            # Ambil yang terpanjang di bagian atas
            title_candidates.sort(key=lambda x: (x[0], -x[2]))
            result["title"] = title_candidates[0][1]
        else:
            # Fallback: ambil baris pertama yang cukup panjang
            for line in lines[:5]:
                if 10 < len(line) < 200:
                    result["title"] = line
                    break
        
        # ===== EXTRACT ABSTRACT =====
        abstract_patterns = [
            r'(?i)^abstract[:\s]*(.+?)(?=\n\n|keywords|introduction|$)',
            r'(?i)^summary[:\s]*(.+?)(?=\n\n|keywords|introduction|$)',
            r'(?i)^overview[:\s]*(.+?)(?=\n\n|keywords|introduction|$)',
        ]
        
        for pattern in abstract_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                abstract_text = match.group(1).strip()
                # Clean abstract
                abstract_text = re.sub(r'\s+', ' ', abstract_text)
                result["abstract"] = abstract_text[:2000]  # Limit length
                break
        
        # Fallback: cari section antara title dan keywords/introduction
        if not result["abstract"]:
            # Find position of title
            title_pos = text.lower().find(result["title"].lower()) if result["title"] else 0
            
            # Find position of keywords or introduction
            keyword_markers = ["keywords", "keyword", "key words", "introduction", "1. introduction"]
            next_section_pos = len(text)
            
            for marker in keyword_markers:
                pos = text.lower().find(marker, title_pos + len(result["title"]))
                if pos != -1 and pos < next_section_pos:
                    next_section_pos = pos
            
            # Extract text between title and next section
            if title_pos < next_section_pos:
                potential_abstract = text[title_pos + len(result["title"]):next_section_pos].strip()
                # Clean dan limit
                potential_abstract = re.sub(r'\s+', ' ', potential_abstract)
                
                # Check if looks like abstract (not too short, not too long)
                if 100 < len(potential_abstract) < 2000:
                    result["abstract"] = potential_abstract
        
        # ===== EXTRACT KEYWORDS =====
        keyword_patterns = [
            r'(?i)keywords?[:\s]*(.+?)(?=\n\n|introduction|abstract|$)',
            r'(?i)key\s*words?[:\s]*(.+?)(?=\n\n|introduction|abstract|$)',
            r'(?i)index\s*terms?[:\s]*(.+?)(?=\n\n|introduction|abstract|$)',
        ]
        
        for pattern in keyword_patterns:
            match = re.search(pattern, text, re.DOTALL | re.MULTILINE)
            if match:
                keywords_text = match.group(1).strip()
                
                # Split keywords by common separators
                keywords = re.split(r'[;,•·\n]+', keywords_text)
                keywords = [kw.strip() for kw in keywords if kw.strip()]
                
                # Clean each keyword
                cleaned_keywords = []
                for kw in keywords:
                    # Remove numbers at start (1., 2., etc)
                    kw = re.sub(r'^\d+[\.\)]\s*', '', kw)
                    # Remove extra spaces
                    kw = re.sub(r'\s+', ' ', kw).strip()
                    # Only keep reasonable length
                    if 2 < len(kw) < 50:
                        cleaned_keywords.append(kw)
                
                result["keywords"] = cleaned_keywords[:20]  # Max 20 keywords
                break
        
        # ===== EXTRACT AUTHORS =====
        # Authors biasanya setelah title, sebelum abstract
        # Pattern: nama dengan inisial atau affiliasi
        author_patterns = [
            r'(?i)^authors?[:\s]*(.+?)(?=\n\n|abstract|keywords|$)',
            r'(?i)^by[:\s]*(.+?)(?=\n\n|abstract|keywords|$)',
        ]
        
        for pattern in author_patterns:
            match = re.search(pattern, text, re.MULTILINE)
            if match:
                authors_text = match.group(1).strip()
                # Split by comma or 'and'
                authors = re.split(r',|\s+and\s+|\n', authors_text)
                authors = [a.strip() for a in authors if a.strip()]
                result["authors"] = authors[:10]  # Max 10 authors
                break
        
        # ===== EXTRACT YEAR =====
        # Look for 4-digit year in first few lines
        year_pattern = r'\b(19|20)\d{2}\b'
        for line in lines[:20]:
            match = re.search(year_pattern, line)
            if match:
                result["year"] = match.group(0)
                break
        
        return result
    
    @staticmethod
    def _extract_pdf(file_path: str) -> str:
        """Ekstrak PDF dengan pdfplumber (lebih baik)"""
        try:
            text = ""
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
            
            # Fallback ke PyPDF2 jika pdfplumber gagal
            if not text.strip():
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n\n"
            
            return text.strip()
        except Exception as e:
            logger.error(f"PDF extraction error: {str(e)}")
            return ""
    
    @staticmethod
    def _extract_docx(file_path: str) -> str:
        """Ekstrak dari DOCX"""
        try:
            doc = Document(file_path)
            full_text = []
            
            # Paragraf
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text.append(para.text)
            
            # Tabel
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            full_text.append(cell.text)
            
            return "\n".join(full_text)
        except Exception as e:
            logger.error(f"DOCX extraction error: {str(e)}")
            return ""
    
    @staticmethod
    def _extract_doc(file_path: str) -> str:
        """Basic extraction untuk DOC"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                # Coba decode
                for encoding in ['utf-8', 'latin-1', 'windows-1252', 'cp1252']:
                    try:
                        text = content.decode(encoding, errors='ignore')
                        # Ambil bagian yang mirip teks (min 3 karakter)
                        lines = [line.strip() for line in text.split('\n') 
                                if len(line.strip()) > 3]
                        return "\n".join(lines)
                    except:
                        continue
                return "Tidak dapat mengekstrak teks dari file .doc"
        except Exception as e:
            logger.error(f"DOC extraction error: {str(e)}")
            return ""
    
    @staticmethod
    def _extract_text(file_path: str) -> str:
        """Baca file teks biasa"""
        try:
            for encoding in ['utf-8', 'latin-1', 'windows-1252', 'cp1252']:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        if content.strip():
                            return content
                except UnicodeDecodeError:
                    continue
            
            # Jika semua encoding gagal, coba binary
            with open(file_path, 'rb') as f:
                content = f.read()
                return content.decode('utf-8', errors='ignore')
                
        except Exception as e:
            logger.error(f"Text extraction error: {str(e)}")
            return ""
    
    def is_supported(self, filename: str) -> bool:
        """Cek apakah format file didukung"""
        _, ext = os.path.splitext(filename.lower())
        return ext in self.supported_extensions


# ===== TESTING CODE =====
if __name__ == "__main__":
    import sys
    
    print("\n" + "="*70)
    print("DOCUMENT EXTRACTOR TEST")
    print("="*70)
    
    # Test with a sample text
    sample_paper = """
RENEWABLE ENERGY SYSTEMS FOR SUSTAINABLE DEVELOPMENT

John Doe¹, Jane Smith², Michael Johnson³

¹Department of Environmental Science, University of ABC
²Institute of Renewable Energy, XYZ Research Center
³School of Engineering, DEF University

2023

ABSTRACT

This paper explores the role of renewable energy systems in achieving sustainable 
development goals. We analyze solar, wind, and hydroelectric power generation 
technologies and their environmental impacts. Our findings demonstrate that 
transitioning to renewable energy sources can significantly reduce carbon emissions 
while promoting economic growth and energy security.

KEYWORDS: renewable energy, sustainable development, solar power, wind energy, 
carbon emissions, climate change, energy transition, green technology

1. INTRODUCTION

The global energy landscape is undergoing a fundamental transformation...
    """
    
    # Test structure parsing
    print("\n📄 Testing structure parsing...")
    extractor = DocumentExtractor()
    structured = extractor._parse_structure(sample_paper)
    
    print("\n✅ EXTRACTED STRUCTURE:")
    print(f"\n📌 Title: {structured['title']}")
    print(f"\n📝 Abstract: {structured['abstract'][:200]}...")
    print(f"\n🏷️  Keywords ({len(structured['keywords'])}): {', '.join(structured['keywords'][:5])}")
    print(f"\n👥 Authors ({len(structured['authors'])}): {', '.join(structured['authors'])}")
    print(f"\n📅 Year: {structured['year']}")
    print(f"\n📊 Full text length: {len(structured['full_text'])} chars")
    
    print("\n" + "="*70)
    print("✓ Test completed!")
    print("="*70)

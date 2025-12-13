import os
import PyPDF2
import pdfplumber
from docx import Document
import logging
import tempfile
from typing import Tuple

logger = logging.getLogger(__name__)

class DocumentExtractor:
    """Ekstrak teks dari berbagai format dokumen"""
    
    def __init__(self):
        self.supported_extensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.md']
    
    @staticmethod
    def extract_from_bytes(file_bytes: bytes, filename: str) -> Tuple[str, str, bool]:
        """Ekstrak teks dari bytes file"""
        try:
            # Validasi nama file
            if not filename or filename.strip() == '':
                return "", "Nama file tidak valid", False
            
            # Dapatkan ekstensi
            _, ext = os.path.splitext(filename)
            ext = ext.lower()
            
            # Validasi ekstensi
            supported_ext = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.md']
            if ext not in supported_ext:
                return "", f"Format tidak didukung: {ext}. Format yang didukung: {', '.join(supported_ext)}", False
            
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
                # Hapus file temporary
                os.unlink(tmp_path)
                return "", f"Format tidak didukung: {ext}", False
            
            # Hapus file temporary
            os.unlink(tmp_path)
            
            # Validasi hasil ekstraksi
            if not text or not text.strip():
                return "", "Teks kosong setelah ekstraksi", False
            
            return text, file_type, True
            
        except Exception as e:
            logger.error(f"Extraction error for {filename}: {str(e)}")
            # Bersihkan file temporary jika ada error
            if 'tmp_path' in locals():
                try:
                    os.unlink(tmp_path)
                except:
                    pass
            return "", f"Error ekstraksi: {str(e)}", False
    
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
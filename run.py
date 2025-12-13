#!/usr/bin/env python3
"""
Script untuk menjalankan aplikasi SDGs Extractor secara lokal
"""

import os
import sys
import webbrowser
import threading
import time

def check_dependencies():
    """Cek apakah semua dependensi terinstall"""
    try:
        import flask
        import torch
        import transformers
        import PyPDF2
        print("✓ Semua dependensi terinstall")
        return True
    except ImportError as e:
        print(f"✗ Error: {e}")
        print("\nInstal dependensi dengan:")
        print("  pip install -r requirements.txt")
        return False

def open_browser():
    """Buka browser otomatis setelah server siap"""
    time.sleep(2)  # Tunggu server startup
    webbrowser.open("http://localhost:5000")

def main():
    print("\n" + "="*60)
    print("SDGs DOCUMENT EXTRACTOR - LOCAL SERVER")
    print("="*60)
    
    # Cek dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Jalankan server
    print("\nMenjalankan server...")
    print("Tekan Ctrl+C untuk berhenti")
    print("\nAkses di browser:")
    print("  • http://localhost:5000")
    print("  • http://127.0.0.1:5000")
    
    # Buka browser otomatis
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Jalankan app
    os.system("python app.py")

if __name__ == "__main__":
    main()
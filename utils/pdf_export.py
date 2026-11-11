import pypdf
import markdown
from fpdf import FPDF
import streamlit as st
import re

def extract_text_from_file(uploaded_file):
    if uploaded_file is None: return ""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_extension == 'pdf':
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                if page.extract_text(): 
                    text += page.extract_text() + "\n"
            return text.strip()
        else:
            return uploaded_file.read().decode("utf-8").strip()
    except Exception as e:
        st.error(f"Error reading file {uploaded_file.name}: {e}")
        return ""

def generate_pdf(text_content):
    # Převedeme Markdown na základní strukturu, kterou fpdf2 zvládne
    # Pro jednoduchost zde budeme Markdown interpretovat po řádcích.
    
    pdf = FPDF()
    pdf.add_page()
    
    # Registrace fontu pro českou diakritiku
    # Předpokládáme, že DejaVu fonty jsou dostupné nebo je můžeme přidat.
    # Pro Streamlit Cloud je nejlepší použít standardní fonty, ale pro diakritiku
    # je potřeba přidat .ttf soubor. Zde použijeme trik s core fontem,
    # ale pro plnou podporu češtiny byste museli nahrát .ttf soubor do projektu.
    # Prozatím použijeme Helvetica, která má základní podporu.
    
    pdf.set_font("Helvetica", size=11)
    
    # Zpracování řádek po řádku
    lines = text_content.split('\n')
    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5) # Prázdný řádek
            continue
            
        # Velmi jednoduchá detekce nadpisů
        if line.startswith('# '):
            pdf.set_font("Helvetica", 'B', 16)
            pdf.multi_cell(0, 10, line[2:])
            pdf.set_font("Helvetica", size=11)
            pdf.ln(2)
        elif line.startswith('## '):
            pdf.set_font("Helvetica", 'B', 14)
            pdf.multi_cell(0, 8, line[3:])
            pdf.set_font("Helvetica", size=11)
            pdf.ln(2)
        elif line.startswith('### '):
            pdf.set_font("Helvetica", 'B', 12)
            pdf.multi_cell(0, 7, line[4:])
            pdf.set_font("Helvetica", size=11)
            pdf.ln(2)
        elif line.startswith('- ') or line.startswith('* '):
            pdf.multi_cell(0, 6, "• " + line[2:])
        else:
            # Obyčejný text
            pdf.multi_cell(0, 6, line)
            
    try:
        # Výstup jako bajty
        return pdf.output(dest='S').encode('latin-1') # fpdf2 vrací str, potřebujeme bytes
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return b""

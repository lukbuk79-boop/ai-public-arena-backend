import pypdf
import markdown
from weasyprint import HTML, CSS
import streamlit as st

def extract_text_from_file(uploaded_file):
    if uploaded_file is None: return ""
    file_extension = uploaded_file.name.split('.')[-1].lower()
    try:
        if file_extension == 'pdf':
            pdf_reader = pypdf.PdfReader(uploaded_file)
            text = ""
            for page in pdf_reader.pages:
                if page.extract_text(): text += page.extract_text() + "\n"
            return text.strip()
        else:
            return uploaded_file.read().decode("utf-8").strip()
    except Exception as e:
        st.error(f"Error reading file {uploaded_file.name}: {e}")
        return ""

def generate_pdf(text_content):
    html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
    css_style = """
    @page { size: A4; margin: 2cm; @bottom-center { content: "Page " counter(page) " of " counter(pages); font-size: 9pt; color: #666; } }
    body { font-family: 'DejaVu Sans', sans-serif; font-size: 11pt; line-height: 1.5; color: #333; }
    h1 { color: #1a365d; font-size: 22pt; border-bottom: 2px solid #3182ce; padding-bottom: 5px; margin-top: 25px; }
    h2 { color: #2c5282; font-size: 16pt; margin-top: 20px; }
    h3 { color: #2b6cb0; font-size: 13pt; margin-top: 15px; }
    p { margin-bottom: 10px; text-align: justify; }
    small { color: #718096; font-size: 9pt; display: block; margin-top: 5px; font-style: italic; }
    blockquote { border-left: 4px solid #cbd5e0; padding-left: 15px; color: #4a5568; font-style: italic; background-color: #f7fafc; padding: 10px 15px; margin: 10px 0; }
    table { width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 10pt; }
    th, td { border: 1px solid #e2e8f0; padding: 8px 12px; text-align: left; }
    th { background-color: #edf2f7; font-weight: bold; color: #2d3748; }
    tr:nth-child(even) { background-color: #f7fafc; }
    """
    full_html = f"<!DOCTYPE html><html lang='cs'><head><meta charset='utf-8'></head><body>{html_body}</body></html>"
    try:
        return HTML(string=full_html).write_pdf(stylesheets=[CSS(string=css_style)])
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return b""

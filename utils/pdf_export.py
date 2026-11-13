import pypdf
import markdown
from weasyprint import HTML, CSS
import streamlit as st
import base64
import os
from datetime import datetime

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

def get_logo_base64():
    """Převede logo na base64, aby ho WeasyPrint našel všude."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "..", "ai_arena.png")
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        pass
    return ""

def generate_pdf(text_content, topic=None):
    if topic is None:
        topic = st.session_state.get("current_topic", "AI Aréna")

    # 1. Příprava HTML z Markdownu
    html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
    
    # 2. Logo jako base64 pro CSS
    logo_b64 = get_logo_base64()
    logo_data_uri = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""
    
    # 3. Získání aktuálního data
    current_date = datetime.now().strftime("%d.%m.%Y")

    # 4. HTML pro titulní stranu
    cover_html = f"""
    <div class="cover-page">
        {'<img src="' + logo_data_uri + '" class="cover-logo" />' if logo_b64 else ''}
        <h1 class="cover-title">{topic}</h1>
        <p class="cover-subtitle">Debata vygenerovaná AI Arénou</p>
        <p class="cover-date">{current_date}</p>
    </div>
    """

    # 5. Kompletní HTML dokument
    full_html = f"""
    <!DOCTYPE html>
    <html lang='cs'>
    <head><meta charset='utf-8'></head>
    <body>
        {cover_html}
        <div class="content">
            {html_body}
        </div>
    </body>
    </html>
    """

    # 6. CSS styly (červená + zlatá)
    css_style = f"""
    @page {{
        size: A4;
        margin: 2.5cm 2cm 2.5cm 2cm;
        @top-left {{
            content: "{topic}";
            font-family: 'DejaVu Sans', sans-serif;
            font-size: 9pt;
            color: #718096;
            margin-top: 1cm;
        }}
        @top-right {{
            content: url("{logo_data_uri}");
            width: 40px;
            margin-top: 0.5cm;
        }}
        @bottom-left {{
            content: "arena.buchvald.cz  |  info@buchvald.cz";
            font-family: 'DejaVu Sans', sans-serif;
            font-size: 8pt;
            color: #a0aec0;
        }}
        @bottom-right {{
            content: "Strana " counter(page) " z " counter(pages);
            font-family: 'DejaVu Sans', sans-serif;
            font-size: 8pt;
            color: #a0aec0;
        }}
    }}
    
    /* Speciální styly pro první stránku (titulní) */
    @page :first {{
        margin: 0;
        @top-left {{ content: none; }}
        @top-right {{ content: none; }}
        @bottom-left {{ content: none; }}
        @bottom-right {{ content: none; }}
    }}

    body {{
        font-family: 'DejaVu Sans', sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #2d3748;
    }}

    /* --- TITULNÍ STRANA --- */
    .cover-page {{
        page-break-after: always;
        text-align: center;
        padding-top: 150px;
        background: linear-gradient(135deg, #0a0a0c 0%, #1a1a24 100%);
        color: white;
        height: 100%;
    }}
    .cover-logo {{
        width: 220px;
        margin-bottom: 50px;
        filter: drop-shadow(0 0 20px rgba(255, 51, 51, 0.6));
    }}
    .cover-title {{
        color: #ff3333;
        font-size: 26pt;
        font-weight: bold;
        margin-bottom: 15px;
        padding: 0 2cm;
    }}
    .cover-subtitle {{
        color: #a0aec0;
        font-size: 14pt;
        margin-bottom: 10px;
    }}
    .cover-date {{
        color: #ffb300;
        font-size: 12pt;
        margin-top: 80px;
    }}

    /* --- OBSAH --- */
    .content h1 {{
        color: #ff3333;
        font-size: 22pt;
        border-bottom: 3px solid #ffb300;
        padding-bottom: 10px;
        margin-top: 30px;
        page-break-after: avoid;
    }}
    .content h2 {{
        color: #ff3333;
        font-size: 16pt;
        margin-top: 25px;
        page-break-after: avoid;
    }}
    .content h3 {{
        color: #ff5555;
        font-size: 13pt;
        margin-top: 15px;
        page-break-after: avoid;
    }}
    .content p {{
        margin-bottom: 10px;
        text-align: justify;
    }}
    .content small {{
        color: #718096;
        font-size: 9pt;
        display: block;
        margin-top: 5px;
        font-style: italic;
    }}
    .content blockquote {{
        border-left: 4px solid #ffb300;
        background-color: #fff8e1;
        padding: 12px 18px;
        margin: 12px 0;
        color: #4a5568;
        font-style: italic;
    }}
    .content table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 10pt;
    }}
    .content th, .content td {{
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        text-align: left;
    }}
    .content th {{
        background-color: #ff3333;
        color: white;
        font-weight: bold;
    }}
    .content tr:nth-child(even) {{
        background-color: #fff8f8;
    }}
    """

    try:
        return HTML(string=full_html).write_pdf(stylesheets=[CSS(string=css_style)])
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return b""

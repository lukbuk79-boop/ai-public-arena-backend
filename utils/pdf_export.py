import pypdf
import markdown
from weasyprint import HTML, CSS
import streamlit as st
import base64
import os
from datetime import datetime
from PIL import Image
import io

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

def get_watermark_base64():
    """Vytvoří z loga poloprůhledný vodoznak a odstraní případné černé pozadí."""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "..", "ai_arena.png")
        
        if os.path.exists(logo_path):
            img = Image.open(logo_path).convert("RGBA")
            
            # Zmenšení obrázku (šetří RAM, 600px stačí pro 750px vodoznak)
            img.thumbnail((800, 800), Image.Resampling.LANCZOS)
            
            datas = img.getdata()
            new_data = []
            for item in datas:
                r, g, b, a = item
                
                # 1. Pokud je pixel velmi tmavý (černé pozadí), uděláme ho zcela průhledným
                if r < 15 and g < 15 and b < 15:
                    new_data.append((r, g, b, 0))
                else:
                    # 2. Zbytek loga ztlumíme (zachováme průhlednost, ale snížíme ji na cca 15 %)
                    new_data.append((r, g, b, int(a * 0.15)))
            
            img.putdata(new_data)
            
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            return base64.b64encode(buffered.getvalue()).decode("utf-8")
    except Exception as e:
        st.warning(f"Nepodařilo se vytvořit vodoznak: {e}")
    return ""

def get_logo_base64():
    """Načte originální logo pro titulní stranu."""
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

    html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
    
    logo_b64 = get_logo_base64()
    logo_data_uri = f"data:image/png;base64,{logo_b64}" if logo_b64 else ""

    watermark_b64 = get_watermark_base64()
    watermark_uri = f"data:image/png;base64,{watermark_b64}" if watermark_b64 else ""

    current_date = datetime.now().strftime("%d.%m.%Y")

    cover_html = f"""
    <div class="cover-page">
        {'<img src="' + logo_data_uri + '" class="cover-logo" />' if logo_b64 else ''}
        <h1 class="cover-title">{topic}</h1>
        <p class="cover-subtitle">Debata vygenerovaná AI Arénou</p>
        <p class="cover-date">{current_date}</p>
    </div>
    """

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

    css_style = f"""
    @page {{
        size: A4;
        margin: 2.5cm 2cm 2.5cm 2cm;
        
        /* VODOTISK – nativní pozadí stránky (vycentrované, zvětšeno na 750px) */
        background-image: url("{watermark_uri}");
        background-repeat: no-repeat;
        background-position: center center;
        background-size: 750px auto; 
        
        @top-left {{
            content: "{topic}";
            font-family: 'DejaVu Sans', sans-serif;
            font-size: 9pt;
            color: #718096;
            margin-top: 1cm;
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
    
    @page :first {{
        margin: 0;
        background-color: #0a0a0c;
        background-image: none;
        @top-left {{ content: none; }}
        @bottom-left {{ content: none; }}
        @bottom-right {{ content: none; }}
    }}

    body {{
        font-family: 'DejaVu Sans', sans-serif;
        font-size: 11pt;
        line-height: 1.5;
        color: #2d3748;
        word-wrap: break-word;
        overflow-wrap: break-word;
    }}

    .content {{
        width: 100%;
        box-sizing: border-box;
    }}

    /* --- TITULNÍ STRANA --- */
    .cover-page {{
        page-break-after: always;
        width: 100%;
        height: 100%;
        text-align: center;
        padding-top: 200px;
        box-sizing: border-box;
    }}
    .cover-logo {{
        width: 280px;
        margin-bottom: 60px;
        filter: drop-shadow(0 0 30px rgba(255, 51, 51, 0.5)); 
    }}
    .cover-title {{
        color: #ff3333;
        font-size: 28pt;
        font-weight: bold;
        margin-bottom: 20px;
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
        margin-top: 100px;
    }}

    /* --- OBSAH --- */
    .content h1 {{
        color: #ff3333;
        font-size: 22pt;
        border-bottom: 3px solid #ffb300;
        padding-bottom: 10px;
        margin-top: 30px;
        page-break-after: avoid;
        word-wrap: break-word;
    }}
    .content h2 {{
        color: #ff3333;
        font-size: 16pt;
        margin-top: 25px;
        page-break-after: avoid;
        word-wrap: break-word;
    }}
    .content h3 {{
        color: #ff5555;
        font-size: 13pt;
        margin-top: 15px;
        page-break-after: avoid;
        word-wrap: break-word;
    }}
    .content p {{
        margin-bottom: 10px;
        text-align: justify;
        word-wrap: break-word;
        overflow-wrap: break-word;
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
        word-wrap: break-word;
    }}
    .content table {{
        width: 100%;
        border-collapse: collapse;
        margin: 15px 0;
        font-size: 10pt;
        table-layout: fixed;
        word-wrap: break-word;
    }}
    .content th, .content td {{
        border: 1px solid #e2e8f0;
        padding: 8px 12px;
        text-align: left;
        word-wrap: break-word;
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

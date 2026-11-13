import pypdf
import markdown
import pymupdf
import streamlit as st

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

def generate_pdf(text_content, topic=None):
    if topic is None:
        topic = st.session_state.get("current_topic", "AI Aréna")

    try:
        # Převod Markdownu na HTML
        html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
        
        # Základní CSS (barvy a formátování)
        css = """
        body { font-family: sans-serif; font-size: 11pt; color: #2d3748; }
        h1 { color: #ff3333; font-size: 18pt; margin-top: 20px; }
        h2 { color: #ff3333; font-size: 14pt; margin-top: 15px; }
        h3 { color: #ff5555; font-size: 12pt; margin-top: 10px; }
        p { margin-bottom: 10px; text-align: justify; }
        small { color: #718096; font-style: italic; font-size: 9pt; }
        blockquote { border-left: 3px solid #ffb300; background-color: #fff8e1; padding: 10px; color: #4a5568; }
        table { border-collapse: collapse; width: 100%; margin-bottom: 15px; }
        th { background-color: #ff3333; color: white; padding: 8px; border: 1px solid #e2e8f0; }
        td { padding: 8px; border: 1px solid #e2e8f0; }
        """
        
        # Vytvoření dokumentu a stránky A4
        doc = pymupdf.open()
        page = doc.new_page()
        rect = pymupdf.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
        
        # Vložení HTML (scale_low=0.3 zmenší text až na 30 %, aby se vešel)
        result = page.insert_htmlbox(rect, html_body, css=css, scale_low=0.3)
        
        # OPRAVA: result je tuple (spare_height, scale). Kontrolujeme první hodnotu.
        if isinstance(result, tuple) and result[0] < 0:
            st.warning("Text je příliš dlouhý a na stránku se zcela nevešel. PDF bude obsahovat jen to, co se vešlo.")

        # Uložení do bajtů – používáme write() pro větší spolehlivost
        pdf_bytes = doc.write()
        doc.close()
        
        if not pdf_bytes or len(pdf_bytes) < 500:
            st.error("Vygenerované PDF je prázdné nebo příliš malé.")
            return b""
            
        return pdf_bytes

    except Exception as e:
        st.error(f"PDF generation error: {e}")
        return b""

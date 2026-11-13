import pypdf
import markdown
import pymupdf
import os
import streamlit as st
import base64

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
    """Převede logo na base64 string, aby ho PDF engine spolehlivě našel."""
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
        
    logo_b64 = get_logo_base64()
    logo_img_tag = f'<img src="data:image/png;base64,{logo_b64}" class="cover-logo" />' if logo_b64 else ''

    # 1. ZÁKLADNÍ PŘÍPRAVA HTML A CSS
    html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
    
    title_html = f"""
    <html><body>
        <div class="title-page">
            {logo_img_tag}
            <h1 class="cover-title">{topic}</h1>
            <p class="cover-subtitle">Debata vygenerovaná AI Arénou</p>
            <p class="cover-footer">arena.buchvald.cz</p>
        </div>
    </body></html>"""

    content_html = f"""<html><body><div class="content">{html_body}</div></body></html>"""
    
    css = """
    body { font-family: sans-serif; font-size: 11pt; color: #2d3748; }
    .title-page { text-align: center; padding-top: 100px; }
    .cover-logo { width: 220px; margin-bottom: 60px; }
    .cover-title { color: #ff3333; font-size: 26pt; margin-bottom: 15px; }
    .cover-subtitle { color: #666; font-size: 13pt; }
    .cover-footer { color: #ffb300; font-size: 11pt; margin-top: 60px; }
    .content h1 { color: #ff3333; font-size: 20pt; border-bottom: 3px solid #ffb300; padding-bottom: 8px; margin-top: 20px; }
    .content h2 { color: #ff3333; font-size: 15pt; margin-top: 15px; }
    .content h3 { color: #ff5555; font-size: 12pt; margin-top: 10px; }
    .content p { text-align: justify; margin-bottom: 10px; }
    .content small { color: #718096; font-style: italic; font-size: 9pt; }
    .content blockquote { border-left: 4px solid #ffb300; background-color: #fff8e1; padding: 10px 15px; color: #4a5568; }
    .content table { border-collapse: collapse; width: 100%; margin-bottom: 15px; }
    .content th { background-color: #ff3333; color: white; padding: 8px; border: 1px solid #e2e8f0; }
    .content td { padding: 8px; border: 1px solid #e2e8f0; }
    """

    try:
        # 2. POKUS O PLNOHODNOTNÉ PDF POMOCÍ STORY
        doc = pymupdf.open()
        a4 = pymupdf.paper_rect("a4")
        
        # Titulní strana
        title_story = pymupdf.Story(html=title_html, user_css=css)
        title_page = doc.new_page(width=a4.width, height=a4.height)
        title_story.place(title_page.rect)
        title_story.draw(title_page)
        
        # Obsah
        content_story = pymupdf.Story(html=content_html, user_css=css)
        
        margin_side = 50
        margin_top = 80
        margin_bottom = 70
        content_rect = pymupdf.Rect(margin_side, margin_top, a4.width - margin_side, a4.height - margin_bottom)
        
        page_num = 1
        more = True
        
        while more:
            more, filled = content_story.place(content_rect)
            if not filled:
                break
            
            page = doc.new_page(width=a4.width, height=a4.height)
            content_story.draw(page)
            
            # Hlavička (pokud je logo k dispozici)
            if logo_b64:
                try:
                    logo_bytes = base64.b64decode(logo_b64)
                    page.insert_image(pymupdf.Rect(a4.width - 100, 15, a4.width - 20, 60), stream=logo_bytes)
                except Exception:
                    pass
            
            # Téma vlevo
            try:
                page.insert_textbox(pymupdf.Rect(50, 25, a4.width - 120, 55), topic, fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5), align=0)
            except Exception:
                pass # Pokud text box selže (např. kvůli délce), ignorujeme hlavičku
            
            # Červená linka
            page.draw_line(pymupdf.Point(margin_side, 65), pymupdf.Point(a4.width - margin_side, 65), color=(1, 0.2, 0.2), width=1)
            
            # Patička
            page.draw_line(pymupdf.Point(margin_side, a4.height - 55), pymupdf.Point(a4.width - margin_side, a4.height - 55), color=(0.8, 0.8, 0.8), width=0.5)
            try:
                page.insert_textbox(pymupdf.Rect(margin_side, a4.height - 50, a4.width - margin_side, a4.height - 25), f"AI Aréna  ·  arena.buchvald.cz  ·  Strana {page_num}", fontsize=9, fontname="helv", color=(0.5, 0.5, 0.5), align=1)
            except Exception:
                pass
            
            page_num += 1
            if not more:
                break
                
        pdf_bytes = doc.tobytes()
        doc.close()
        
        # Pokud se z nějakého důvodu vygenerovalo 0 bajtů, vyhodíme výjimku pro Fallback
        if not pdf_bytes or len(pdf_bytes) < 1000:
            raise ValueError("Story vygeneroval prázdné PDF.")
            
        return pdf_bytes

    except Exception as e:
        # 3. FALLBACK: Pokud Story selže, vygenerujeme PDF jednodušším a odolnějším způsobem
        try:
            doc = pymupdf.open()
            page = doc.new_page()
            rect = pymupdf.Rect(50, 50, page.rect.width - 50, page.rect.height - 50)
            
            # Jednoduchý převod markdownu na HTML pro insert_htmlbox
            simple_html = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
            
            # insert_htmlbox je velmi odolný, zmenší text, aby se vešel
            page.insert_htmlbox(rect, simple_html, css="body { font-family: sans-serif; font-size: 11pt; }", scale_low=0.4)
            
            pdf_bytes = doc.tobytes()
            doc.close()
            return pdf_bytes
            
        except Exception as fallback_e:
            # 4. POSLEDNÍ ZÁCHRANA: Čistě textové PDF
            try:
                doc = pymupdf.open()
                page = doc.new_page()
                page.insert_textbox(pymupdf.Rect(50, 50, page.rect.width - 50, page.rect.height - 50), text_content[:5000], fontsize=10)
                pdf_bytes = doc.tobytes()
                doc.close()
                return pdf_bytes
            except Exception:
                st.error(f"Kritická chyba PDF: {fallback_e}")
                return b""

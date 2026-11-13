import pypdf
import markdown
import pymupdf
import os
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
    try:
        # Zjištění tématu (pro titulek), pokud není předáno
        if topic is None:
            try:
                topic = st.session_state.get("current_topic", "AI Aréna")
            except:
                topic = "AI Aréna"
        
        # Cesty
        current_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(current_dir, "..", "ai_arena.png")
        has_logo = os.path.exists(logo_path)
        
        # HTML pro titulní stranu
        logo_html = '<img src="ai_arena.png" class="cover-logo" />' if has_logo else ''
        title_html = f"""
        <html><body>
            <div class="title-page">
                {logo_html}
                <h1 class="cover-title">{topic}</h1>
                <p class="cover-subtitle">Debata vygenerovaná AI Arénou</p>
                <p class="cover-footer">arena.buchvald.cz</p>
            </div>
        </body></html>"""
        
        # HTML pro obsah
        html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
        content_html = f"""<html><body><div class="content">{html_body}</div></body></html>"""
        
        # Společné CSS
        css = """
        body { font-family: sans-serif; font-size: 11pt; color: #2d3748; }
        
        /* Titulní strana */
        .title-page {
            text-align: center;
            padding-top: 100px;
        }
        .cover-logo { width: 220px; margin-bottom: 60px; }
        .cover-title { 
            color: #ff3333; 
            font-size: 26pt; 
            margin-bottom: 15px; 
        }
        .cover-subtitle { 
            color: #666; 
            font-size: 13pt; 
        }
        .cover-footer { 
            color: #ffb300; 
            font-size: 11pt; 
            margin-top: 60px; 
        }
        
        /* Obsah */
        .content h1 { 
            color: #ff3333; 
            font-size: 20pt; 
            border-bottom: 3px solid #ffb300; 
            padding-bottom: 8px; 
        }
        .content h2 { color: #ff3333; font-size: 15pt; }
        .content h3 { color: #ff5555; font-size: 12pt; }
        .content p { text-align: justify; margin-bottom: 10px; }
        .content small { color: #718096; font-style: italic; font-size: 9pt; }
        .content blockquote { 
            border-left: 4px solid #ffb300; 
            background-color: #fff8e1; 
            padding: 10px 15px; 
            color: #4a5568;
        }
        .content table { border-collapse: collapse; width: 100%; }
        .content th { 
            background-color: #ff3333; 
            color: white; 
            padding: 8px; 
            border: 1px solid #e2e8f0;
        }
        .content td { 
            padding: 8px; 
            border: 1px solid #e2e8f0; 
        }
        """
        
        # Archive pro logo
        archive = pymupdf.Archive()
        if has_logo:
            archive.add(logo_path)
        
        # Vytvoření dokumentu
        doc = pymupdf.open()
        a4 = pymupdf.paper_rect("a4")
        
        # ============ TITULNÍ STRANA ============
        title_story = pymupdf.Story(html=title_html, user_css=css, archive=archive)
        title_page = doc.new_page(width=a4.width, height=a4.height)
        title_story.place(title_page.rect)
        title_story.draw(title_page)
        
        # ============ OBSAH ============
        content_story = pymupdf.Story(html=content_html, user_css=css, archive=archive)
        
        # Okraje pro obsah (volný prostor pro hlavičku a patičku)
        margin_side = 50
        margin_top = 80
        margin_bottom = 70
        
        content_rect = pymupdf.Rect(
            margin_side,
            margin_top,
            a4.width - margin_side,
            a4.height - margin_bottom
        )
        
        page_num = 1
        more = True
        
        while more:
            more, filled = content_story.place(content_rect)
            if not filled:
                break
            
            page = doc.new_page(width=a4.width, height=a4.height)
            content_story.draw(page)
            
            # === HLAVIČKA (logo vpravo, téma vlevo) ===
            if has_logo:
                header_logo_rect = pymupdf.Rect(
                    a4.width - 100, 15,
                    a4.width - 20, 60
                )
                page.insert_image(header_logo_rect, filename=logo_path)
            
            # Téma vlevo (italsky, šedě)
            page.insert_textbox(
                pymupdf.Rect(50, 25, a4.width - 120, 55),
                topic,
                fontsize=9,
                fontname="helv",
                color=(0.5, 0.5, 0.5),
                align=0  # vlevo
            )
            
            # Červená linka pod hlavičkou
            page.draw_line(
                pymupdf.Point(margin_side, 65),
                pymupdf.Point(a4.width - margin_side, 65),
                color=(1, 0.2, 0.2),
                width=1
            )
            
            # === PATIČKA ===
            # Šedá linka nad patičkou
            page.draw_line(
                pymupdf.Point(margin_side, a4.height - 55),
                pymupdf.Point(a4.width - margin_side, a4.height - 55),
                color=(0.8, 0.8, 0.8),
                width=0.5
            )
            
            # Text patičky
            page.insert_textbox(
                pymupdf.Rect(margin_side, a4.height - 50, a4.width - margin_side, a4.height - 25),
                f"AI Aréna  ·  arena.buchvald.cz  ·  Strana {page_num}",
                fontsize=9,
                fontname="helv",
                color=(0.5, 0.5, 0.5),
                align=1  # center
            )
            
            page_num += 1
            if not more:
                break
        
        pdf_bytes = doc.tobytes()
        doc.close()
        return pdf_bytes
        
    except Exception as e:
        st.error(f"PDF generation error: {e}")
        import traceback
        st.error(traceback.format_exc())
        return b""

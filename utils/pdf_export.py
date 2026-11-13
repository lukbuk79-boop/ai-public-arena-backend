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
        # 1. Převod Markdownu na HTML
        html_body = markdown.markdown(text_content, extensions=['tables', 'nl2br'])
        full_html = f"<html><body>{html_body}</body></html>"
        
        # 2. CSS styl
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
        
        # 3. Vytvoření dokumentu a Story
        doc = pymupdf.open()
        story = pymupdf.Story(html=full_html, user_css=css)
        
        # 4. Formát A4 a okraje
        page_rect = pymupdf.paper_rect("a4")
        margin = 50
        content_rect = pymupdf.Rect(margin, margin, page_rect.width - margin, page_rect.height - margin)
        
        # 5. Smyčka pro vykreslování na více stránek
        more = True
        while more:
            page = doc.new_page(width=page_rect.width, height=page_rect.height)
            more, filled = story.place(content_rect)
            if not filled:
                break
            story.draw(page)
        
        # 6. Uložení
        pdf_bytes = doc.write()
        doc.close()
        
        if not pdf_bytes or len(pdf_bytes) < 500:
            st.error("Vygenerované PDF je prázdné.")
            return b""
            
        return pdf_bytes

    except Exception as e:
        st.error(f"PDF generation error: {e}")
        import traceback
        st.error(traceback.format_exc())
        return b""

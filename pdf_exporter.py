from fpdf import FPDF
from io import BytesIO
import os

FONT_PATH = os.path.join("fonts", "DejaVuSans.ttf")  # Ensure font file exists in this path

def break_long_words(text, max_len=60):
    if not isinstance(text, str):
        text = str(text)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('—', '-')  # Replace problematic characters
    safe_words = []
    for word in text.split():
        if len(word) > max_len:
            safe_words.extend([word[i:i+max_len] for i in range(0, len(word), max_len)])
        else:
            safe_words.append(word)
    return ' '.join(safe_words)

def generate_pdf_report(title, transcript, sentiment, keywords, qa_results, qa_results_nlp):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)
    pdf.set_font("DejaVu", size=12)

    def add_multiline(label, text, bold=True):
        pdf.set_font("DejaVu", "B" if bold else "", 12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, break_long_words(text))
        pdf.ln()

    # Title
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, break_long_words(title), ln=True)
    pdf.ln()

    add_multiline("Transcript:", transcript)
    add_multiline("Sentiment:", sentiment)

    # Keywords
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Keywords:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    if keywords:
        for kw in sorted(set(keywords)):
            pdf.cell(0, 10, f"- {break_long_words(kw)}", ln=True)
    else:
        pdf.cell(0, 10, "None", ln=True)
    pdf.ln()

    # QA Scoring
    def add_qa_section(title, results):
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, title, ln=True)
        pdf.set_font("DejaVu", "", 12)
        for section, result in results.items():
            line = f"- {section}: {result['score']} — {result['explanation']}"
            pdf.multi_cell(0, 10, break_long_words(line))
        pdf.ln()

    add_qa_section("Rule-Based QA Scoring:", qa_results)
    add_qa_section("NLP-Based QA Scoring:", qa_results_nlp)

    # Return BytesIO stream
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest="S").encode("utf-8", "replace")
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    return pdf_bytes


def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)

    def safe_txt(text):
        return break_long_words(str(text))

    for call in call_summaries:
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(0, 10, safe_txt(f"Call Summary – {call['filename']}"), ln=True)
        pdf.ln()

        pdf.set_font("DejaVu", "", 12)
        pdf.multi_cell(0, 10, safe_txt(f"Sentiment: {call['sentiment']}"))
        pdf.ln()

        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "Keywords:", ln=True)
        pdf.set_font("DejaVu", "", 12)
        if call["keywords"]:
            for kw in sorted(set(call["keywords"])):
                pdf.cell(0, 10, f"- {safe_txt(kw)}", ln=True)
        else:
            pdf.cell(0, 10, "None", ln=True)
        pdf.ln()

        # QA Sections
        def write_qa_section(title, results):
            pdf.set_font("DejaVu", "B", 12)
            pdf.cell(0, 10, title, ln=True)
            pdf.set_font("DejaVu", "", 12)
            for section, result in results.items():
                line = f"- {section}: {result['score']} — {result['explanation']}"
                pdf.multi_cell(0, 10, safe_txt(line))
            pdf.ln()

        write_qa_section("Rule-Based QA Scoring:", call["qa_results"])
        write_qa_section("NLP-Based QA Scoring:", call["qa_results_nlp"])

        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "Transcript:", ln=True)
        pdf.set_font("DejaVu", "", 11)
        pdf.multi_cell(0, 10, safe_txt(call["transcript"]))
        pdf.ln()

    # Return BytesIO stream
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest="S").encode("utf-8", "replace")
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    return pdf_bytes

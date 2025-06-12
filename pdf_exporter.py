from fpdf import FPDF
from io import BytesIO
import os

FONT_PATH = os.path.join("fonts", "DejaVuSans.ttf")  # Must exist

def break_long_words(text, max_len=60):
    if not isinstance(text, str):
        text = str(text)
    text = text.replace('\n', ' ').replace('\r', ' ').replace('—', '-')  # Normalize
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

    def section_title(label):
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("DejaVu", "", 12)

    def write_lines(lines):
        for line in lines:
            pdf.multi_cell(0, 10, break_long_words(line))

    # Title
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, break_long_words(title), ln=True)
    pdf.ln()

    # Transcript
    section_title("Transcript:")
    write_lines([transcript])
    pdf.ln()

    # Sentiment
    section_title("Sentiment:")
    write_lines([sentiment])
    pdf.ln()

    # Keywords
    section_title("Keywords:")
    if keywords:
        write_lines([f"- {kw}" for kw in sorted(set(keywords))])
    else:
        write_lines(["None"])
    pdf.ln()

    # Rule-Based QA
    section_title("Rule-Based QA Scoring:")
    lines = [f"- {section}: {result['score']} — {result['explanation']}" for section, result in qa_results.items()]
    write_lines(lines)
    pdf.ln()

    # NLP-Based QA
    section_title("NLP-Based QA Scoring:")
    lines = [f"- {section}: {result['score']} — {result['explanation']}" for section, result in qa_results_nlp.items()]
    write_lines(lines)

    # Return BytesIO
    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S").encode("utf-8", "replace"))
    pdf_bytes.seek(0)
    return pdf_bytes

def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)

    def section_title(label):
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("DejaVu", "", 12)

    def write_lines(lines):
        for line in lines:
            pdf.multi_cell(0, 10, break_long_words(line))

    for call in call_summaries:
        pdf.add_page()

        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(0, 10, break_long_words(f"Call Summary – {call['filename']}"), ln=True)
        pdf.ln()

        section_title("Sentiment:")
        write_lines([call["sentiment"]])
        pdf.ln()

        section_title("Keywords:")
        if call["keywords"]:
            write_lines([f"- {kw}" for kw in sorted(set(call["keywords"]))])
        else:
            write_lines(["None"])
        pdf.ln()

        section_title("Rule-Based QA Scoring:")
        lines = [f"- {section}: {result['score']} — {result['explanation']}" for section, result in call["qa_results"].items()]
        write_lines(lines)
        pdf.ln()

        section_title("NLP-Based QA Scoring:")
        lines = [f"- {section}: {result['score']} — {result['explanation']}" for section, result in call["qa_results_nlp"].items()]
        write_lines(lines)
        pdf.ln()

        section_title("Transcript:")
        write_lines([call["transcript"]])
        pdf.ln()

    # Return BytesIO
    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S").encode("utf-8", "replace"))
    pdf_bytes.seek(0)
    return pdf_bytes

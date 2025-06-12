from fpdf import FPDF
from io import BytesIO
import os

FONT_PATH = os.path.join("fonts", "DejaVuSans.ttf")  # Ensure this file exists

def break_long_words(text, max_len=40):
    words = text.split()
    safe_words = []
    for word in words:
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

    # Title
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, txt=str(title), ln=True)
    pdf.ln()

    # Transcript
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Transcript:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    safe_transcript = break_long_words(str(transcript))
    pdf.multi_cell(0, 10, txt=safe_transcript)
    pdf.ln()

    # Sentiment
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, f"Sentiment: {sentiment}", ln=True)

    # Keywords
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Keywords:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    if keywords:
        for kw in sorted(set(keywords)):
            safe_kw = break_long_words(kw)
            pdf.cell(0, 10, f"- {safe_kw}", ln=True)
    else:
        pdf.cell(0, 10, "None", ln=True)
    pdf.ln()

    # Rule-Based QA
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Rule-Based QA Scoring:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    for section, result in qa_results.items():
        line = f"- {section}: {result['score']} — {result['explanation']}"
        safe_line = break_long_words(line)
        pdf.multi_cell(0, 10, txt=safe_line)
    pdf.ln()

    # NLP-Based QA
    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "NLP-Based QA Scoring:", ln=True)
    pdf.set_font("DejaVu", "", 12)
    for section, result in qa_results_nlp.items():
        line = f"- {section}: {result['score']} — {result['explanation']}"
        safe_line = break_long_words(line)
        pdf.multi_cell(0, 10, txt=safe_line)

    # Output to BytesIO
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest="S").encode("utf-8")
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    return pdf_bytes


def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)

    for call in call_summaries:
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(0, 10, f"Call Summary – {call['filename']}", ln=True)
        pdf.ln()

        pdf.set_font("DejaVu", "", 12)
        sentiment_line = break_long_words(f"Sentiment: {call['sentiment']}")
        pdf.multi_cell(0, 10, sentiment_line)
        pdf.ln()

        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "Keywords:", ln=True)
        pdf.set_font("DejaVu", "", 12)
        if call["keywords"]:
            for kw in sorted(set(call["keywords"])):
                safe_kw = break_long_words(kw)
                pdf.cell(0, 10, f"- {safe_kw}", ln=True)
        else:
            pdf.cell(0, 10, "None", ln=True)
        pdf.ln()

        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "Rule-Based QA Scoring:", ln=True)
        pdf.set_font("DejaVu", "", 12)
        for section, result in call["qa_results"].items():
            line = f"- {section}: {result['score']} — {result['explanation']}"
            safe_line = break_long_words(line)
            pdf.multi_cell(0, 10, txt=safe_line)
        pdf.ln()

        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "NLP-Based QA Scoring:", ln=True)
        pdf.set_font("DejaVu", "", 12)
        for section, result in call["qa_results_nlp"].items():
            line = f"- {section}: {result['score']} — {result['explanation']}"
            safe_line = break_long_words(line)
            pdf.multi_cell(0, 10, txt=safe_line)
        pdf.ln()

        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, "Transcript:", ln=True)
        pdf.set_font("DejaVu", "", 11)
        safe_transcript = break_long_words(str(call["transcript"]))
        pdf.multi_cell(0, 10, txt=safe_transcript)
        pdf.ln()

    # Output to BytesIO
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest="S").encode("utf-8")
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    return pdf_bytes
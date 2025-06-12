from fpdf import FPDF
from io import BytesIO
import os
import textwrap

FONT_PATH = os.path.join("fonts", "DejaVuSans.ttf")  # Ensure this font exists

def wrap_text(text, width=100):
    """Safely wrap very long strings into manageable segments."""
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\n", " ").replace("\r", " ").replace("—", "-")
    return textwrap.fill(text, width)

def generate_pdf_report(title, transcript, sentiment, keywords, qa_results, qa_results_nlp):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)

    def section(label):
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("DejaVu", "", 12)

    def print_lines(lines):
        for line in lines:
            safe = wrap_text(line, width=100)
            pdf.multi_cell(0, 8, safe)

    # Title
    pdf.set_font("DejaVu", "B", 14)
    pdf.cell(0, 10, wrap_text(title), ln=True)
    pdf.ln()

    # Transcript
    section("Transcript:")
    print_lines([transcript])
    pdf.ln()

    # Sentiment
    section("Sentiment:")
    print_lines([sentiment])
    pdf.ln()

    # Keywords
    section("Keywords:")
    if keywords:
        print_lines([f"- {kw}" for kw in sorted(set(keywords))])
    else:
        print_lines(["None"])
    pdf.ln()

    # Rule-Based QA
    section("Rule-Based QA Scoring:")
    lines = [f"- {k}: {v['score']} — {v['explanation']}" for k, v in qa_results.items()]
    print_lines(lines)
    pdf.ln()

    # NLP-Based QA
    section("NLP-Based QA Scoring:")
    lines = [f"- {k}: {v['score']} — {v['explanation']}" for k, v in qa_results_nlp.items()]
    print_lines(lines)

    # Return as BytesIO
    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S").encode("utf-8", "replace"))
    pdf_bytes.seek(0)
    return pdf_bytes

def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", FONT_PATH, uni=True)
    pdf.add_font("DejaVu", "B", FONT_PATH, uni=True)

    def section(label):
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("DejaVu", "", 12)

    def print_lines(lines):
        for line in lines:
            safe = wrap_text(line, width=100)
            pdf.multi_cell(0, 8, safe)

    for call in call_summaries:
        pdf.add_page()
        pdf.set_font("DejaVu", "B", 14)
        pdf.cell(0, 10, wrap_text(f"Call Summary – {call['filename']}"), ln=True)
        pdf.ln()

        section("Sentiment:")
        print_lines([call["sentiment"]])
        pdf.ln()

        section("Keywords:")
        if call["keywords"]:
            print_lines([f"- {kw}" for kw in sorted(set(call["keywords"]))])
        else:
            print_lines(["None"])
        pdf.ln()

        section("Rule-Based QA Scoring:")
        lines = [f"- {k}: {v['score']} — {v['explanation']}" for k, v in call["qa_results"].items()]
        print_lines(lines)
        pdf.ln()

        section("NLP-Based QA Scoring:")
        lines = [f"- {k}: {v['score']} — {v['explanation']}" for k, v in call["qa_results_nlp"].items()]
        print_lines(lines)
        pdf.ln()

        section("Transcript:")
        print_lines([call["transcript"]])
        pdf.ln()

    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S").encode("utf-8", "replace"))
    pdf_bytes.seek(0)
    return pdf_bytes

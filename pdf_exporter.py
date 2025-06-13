from fpdf import FPDF
from io import BytesIO
import textwrap
import unicodedata
import streamlit as st


def sanitize(text):
    """Convert to ASCII-safe characters only (strip Unicode dashes, quotes, etc.)."""
    if not isinstance(text, str):
        text = str(text)
    # Replace smart punctuation with ASCII equivalents
    replacements = {
        "–": "-",  # en dash
        "—": "-",  # em dash
        "“": '"', "”": '"',
        "‘": "'", "’": "'",
        "\u00A0": " ",  # non-breaking space
    }
    for bad, good in replacements.items():
        text = text.replace(bad, good)
    # Remove any remaining accents or incompatible characters
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

def wrap_text(text, width=100):
    """Wrap text into safe lines for PDF."""
    text = sanitize(text).replace("\n", " ").replace("\r", " ")
    return textwrap.wrap(text, width=width) or ["[Empty or invalid line]"]

@st.cache_data
def generate_pdf_report(title, transcript, sentiment, keywords, qa_results, qa_results_nlp):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def section(label):
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, sanitize(label), ln=True)
        pdf.set_font("Arial", size=12)

    def write_lines(lines):
        for line in lines:
            for wrapped in wrap_text(line):
                pdf.cell(0, 10, wrapped, ln=True)

    # Title
    pdf.set_font("Arial", style="B", size=14)
    write_lines([title])
    pdf.ln()

    section("Transcript:")
    write_lines([transcript])
    pdf.ln()

    section("Sentiment:")
    write_lines([sentiment])
    pdf.ln()

    section("Keywords:")
    if keywords:
        write_lines([f"- {kw}" for kw in sorted(set(keywords))])
    else:
        write_lines(["None"])
    pdf.ln()

    section("Rule-Based QA Scoring:")
    write_lines([f"- {k}: {v['score']} - {v['explanation']}" for k, v in qa_results.items()])
    pdf.ln()

    section("NLP-Based QA Scoring:")
    write_lines([f"- {k}: {v['score']} - {v['explanation']}" for k, v in qa_results_nlp.items()])
    pdf.ln()

    # Output
    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S"))
    pdf_bytes.seek(0)
    return pdf_bytes


@st.cache_data
def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    def section(label):
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, sanitize(label), ln=True)
        pdf.set_font("Arial", size=12)

    def write_lines(lines):
        for line in lines:
            for wrapped in wrap_text(line):
                pdf.cell(0, 10, wrapped, ln=True)

    for call in call_summaries:
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=14)
        write_lines([f"Call Summary - {call['filename']}"])
        pdf.ln()

        section("Sentiment:")
        write_lines([call["sentiment"]])
        pdf.ln()

        section("Keywords:")
        if call["keywords"]:
            write_lines([f"- {kw}" for kw in sorted(set(call["keywords"]))])
        else:
            write_lines(["None"])
        pdf.ln()

        section("Rule-Based QA Scoring:")
        write_lines([f"- {k}: {v['score']} - {v['explanation']}" for k, v in call["qa_results"].items()])
        pdf.ln()

        section("NLP-Based QA Scoring:")
        write_lines([f"- {k}: {v['score']} - {v['explanation']}" for k, v in call["qa_results_nlp"].items()])
        pdf.ln()

        section("Transcript:")
        write_lines([call["transcript"]])
        pdf.ln()

    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S"))
    pdf_bytes.seek(0)
    return pdf_bytes

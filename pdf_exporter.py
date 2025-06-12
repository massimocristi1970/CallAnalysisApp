from fpdf import FPDF
from io import BytesIO
import textwrap

def safe_wrap(text, width=100):
    if not isinstance(text, str):
        text = str(text)
    text = text.replace("\n", " ").replace("\r", " ").replace("—", "-")
    return textwrap.wrap(text, width=width) or ["[Unrenderable line]"]

def generate_pdf_report(title, transcript, sentiment, keywords, qa_results, qa_results_nlp):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    def section(label):
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("Arial", size=12)

    def write_lines(lines):
        for line in lines:
            for wrapped in safe_wrap(line):
                pdf.cell(0, 10, wrapped, ln=True)

    # Title
    pdf.set_font("Arial", style="B", size=14)
    write_lines([title])
    pdf.ln()

    # Transcript
    section("Transcript:")
    write_lines([transcript])
    pdf.ln()

    # Sentiment
    section("Sentiment:")
    write_lines([sentiment])
    pdf.ln()

    # Keywords
    section("Keywords:")
    if keywords:
        write_lines([f"- {kw}" for kw in sorted(set(keywords))])
    else:
        write_lines(["None"])
    pdf.ln()

    # Rule-Based QA
    section("Rule-Based QA Scoring:")
    write_lines([f"- {k}: {v['score']} — {v['explanation']}" for k, v in qa_results.items()])
    pdf.ln()

    # NLP-Based QA
    section("NLP-Based QA Scoring:")
    write_lines([f"- {k}: {v['score']} — {v['explanation']}" for k, v in qa_results_nlp.items()])

    # Output as bytes
    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S").encode("latin1", "replace"))
    pdf_bytes.seek(0)
    return pdf_bytes


def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    def section(label):
        pdf.set_font("Arial", style="B", size=12)
        pdf.cell(0, 10, label, ln=True)
        pdf.set_font("Arial", size=12)

    def write_lines(lines):
        for line in lines:
            for wrapped in safe_wrap(line):
                pdf.cell(0, 10, wrapped, ln=True)

    for call in call_summaries:
        pdf.add_page()
        pdf.set_font("Arial", style="B", size=14)
        write_lines([f"Call Summary – {call['filename']}"])
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
        write_lines([f"- {k}: {v['score']} — {v['explanation']}" for k, v in call["qa_results"].items()])
        pdf.ln()

        section("NLP-Based QA Scoring:")
        write_lines([f"- {k}: {v['score']} — {v['explanation']}" for k, v in call["qa_results_nlp"].items()])
        pdf.ln()

        section("Transcript:")
        write_lines([call["transcript"]])
        pdf.ln()

    # Output as bytes
    pdf_bytes = BytesIO()
    pdf_bytes.write(pdf.output(dest="S").encode("latin1", "replace"))
    pdf_bytes.seek(0)
    return pdf_bytes

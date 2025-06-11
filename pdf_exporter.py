from fpdf import FPDF
from io import BytesIO

def generate_pdf_report(title, transcript, sentiment, keywords, qa_results, qa_results_nlp):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Title
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt=str(title), ln=True)
    pdf.ln()

    # Transcript
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Transcript:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=str(transcript))
    pdf.ln()

    # Sentiment
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"Sentiment: {sentiment}", ln=True)

    # Keywords
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Keywords:", ln=True)
    pdf.set_font("Arial", size=12)
    if keywords:
        for kw in sorted(set(keywords)):
            pdf.cell(0, 10, f"- {kw}", ln=True)
    else:
        pdf.cell(0, 10, "None", ln=True)
    pdf.ln()

    # Rule-Based QA
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Rule-Based QA Scoring:", ln=True)
    pdf.set_font("Arial", size=12)
    for section, result in qa_results.items():
        line = f"- {section}: {result['score']} — {result['explanation']}"
        pdf.multi_cell(0, 10, txt=str(line))
    pdf.ln()

    # NLP-Based QA
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "NLP-Based QA Scoring:", ln=True)
    pdf.set_font("Arial", size=12)
    for section, result in qa_results_nlp.items():
        line = f"- {section}: {result['score']} — {result['explanation']}"
        pdf.multi_cell(0, 10, txt=str(line))

    # Return as BytesIO
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest="S").encode("latin1", "replace")
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    return pdf_bytes


def generate_combined_pdf_report(call_summaries):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for call in call_summaries:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Call Summary – {call['filename']}", ln=True)
        pdf.ln()

        # Sentiment
        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Sentiment: {call['sentiment']}")
        pdf.ln()

        # Keywords
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Keywords:", ln=True)
        pdf.set_font("Arial", size=12)
        if call["keywords"]:
            for kw in sorted(set(call["keywords"])):
                pdf.cell(0, 10, f"- {kw}", ln=True)
        else:
            pdf.cell(0, 10, "None", ln=True)
        pdf.ln()

        # Rule-Based QA
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Rule-Based QA Scoring:", ln=True)
        pdf.set_font("Arial", size=12)
        for section, result in call["qa_results"].items():
            line = f"- {section}: {result['score']} — {result['explanation']}"
            pdf.multi_cell(0, 10, txt=str(line))
        pdf.ln()

        # NLP-Based QA
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "NLP-Based QA Scoring:", ln=True)
        pdf.set_font("Arial", size=12)
        for section, result in call["qa_results_nlp"].items():
            line = f"- {section}: {result['score']} — {result['explanation']}"
            pdf.multi_cell(0, 10, txt=str(line))
        pdf.ln()

        # Transcript
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Transcript:", ln=True)
        pdf.set_font("Arial", size=11)
        pdf.multi_cell(0, 10, txt=str(call["transcript"]))
        pdf.ln()

    # Output as stream
    pdf_bytes = BytesIO()
    pdf_output = pdf.output(dest="S").encode("latin1", "replace")
    pdf_bytes.write(pdf_output)
    pdf_bytes.seek(0)
    return pdf_bytes

# pdf_exporter.py
from fpdf import FPDF
from io import BytesIO
from pypdf import PdfReader, PdfWriter


def generate_pdf_report(call_data):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)

    for i, call in enumerate(call_data):
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, f"Call Analysis Report #{i+1}", ln=True)

        pdf.set_font("Arial", "", 12)
        pdf.multi_cell(0, 10, f"Filename: {call['filename']}")
        pdf.multi_cell(0, 10, f"Sentiment: {call['sentiment']}")
        pdf.multi_cell(0, 10, f"Call Type: {call['call_type']}")
        pdf.ln()

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Keywords Detected:", ln=True)
        pdf.set_font("Arial", "", 12)
        if call["keywords"]:
            for kw in call["keywords"]:
                pdf.cell(0, 8, f"- {kw}", ln=True)
        else:
            pdf.cell(0, 8, "None", ln=True)

        pdf.ln()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "QA Scores:", ln=True)
        pdf.set_font("Arial", "", 12)
        for section, result in call["qa_scores"].items():
            pdf.cell(0, 8, f"- {section}: {result['score']} — {result['explanation']}", ln=True)

        pdf.ln()
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Transcript:", ln=True)
        pdf.set_font("Arial", "", 11)
        pdf.multi_cell(0, 8, call["transcript"])

    return pdf.output(dest="S")  # Return bytes, no latin1 encoding

def generate_combined_pdf_report(pdf_list):
    writer = PdfWriter()
    
    for pdf_bytes in pdf_list:
        reader = PdfReader(BytesIO(pdf_bytes))
        for page in reader.pages:
            writer.add_page(page)

    output_stream = BytesIO()
    writer.write(output_stream)
    output_stream.seek(0)
    return output_stream

# pdf_exporter.py
from fpdf import FPDF
from io import BytesIO
from pypdf import PdfReader, PdfWriter
import unicodedata
import logging

# Set up logging to debug text issues
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def sanitize_text(text):
    """Sanitize text for PDF rendering by normalizing and removing unrenderable characters."""
    if text is None or text == "":
        logger.debug("sanitize_text received None or empty text, returning empty string")
        return ""
    try:
        text = str(text)  # Convert to string, handle non-string types
        # Normalize Unicode to decompose combined characters
        text = unicodedata.normalize("NFKD", text)
        # Remove non-printable, control characters, and high-range Unicode
        text = "".join(c for c in text if 32 <= ord(c) < 0xFFFF and c.isprintable())
        logger.debug(f"sanitize_text processed text: {text!r}")
        return text if text.strip() else "N/A"  # Fallback if text is empty after stripping
    except Exception as e:
        logger.error(f"sanitize_text failed: {str(e)}")
        return "N/A"  # Fallback on error

def generate_pdf_report(call_data):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)

        for i, call in enumerate(call_data):
            pdf.add_page()
            pdf.set_font("Arial", "B", 14)
            pdf.cell(0, 10, sanitize_text(f"Call Analysis Report #{i+1}"), ln=True)

            pdf.set_font("Arial", "", 12)
            pdf.multi_cell(0, 10, sanitize_text(f"Filename: {call['filename']}"))
            pdf.multi_cell(0, 10, sanitize_text(f"Sentiment: {call['sentiment']}"))
            pdf.multi_cell(0, 10, sanitize_text(f"Call Type: {call['call_type']}"))
            pdf.ln()

            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, sanitize_text("Keywords Detected:"), ln=True)
            pdf.set_font("Arial", "", 12)
            if call["keywords"]:
                for kw in call["keywords"]:
                    pdf.cell(0, 8, sanitize_text(f"- {kw}"), ln=True)
            else:
                pdf.cell(0, 8, sanitize_text("None"), ln=True)

            pdf.ln()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, sanitize_text("QA Scores:"), ln=True)
            pdf.set_font("Arial", "", 12)
            for section, result in call["qa_scores"].items():
                pdf.cell(0, 8, sanitize_text(f"- {section}: {result['score']} — {result['explanation']}"), ln=True)

            pdf.ln()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, sanitize_text("Transcript:"), ln=True)
            pdf.set_font("Arial", "", 11)
            pdf.multi_cell(0, 8, sanitize_text(call["transcript"]))

        return pdf.output(dest="S")  # Return bytes
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        raise Exception(f"Failed to generate PDF: {str(e)}")

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

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
        logger.debug("sanitize_text received None or empty text, returning 'N/A'")
        return "N/A"
    try:
        text = str(text)  # Convert to string, handle non-string types
        # Normalize Unicode to decompose combined characters
        text = unicodedata.normalize("NFKD", text)
        # Remove non-printable, control characters, zero-width, and high-range Unicode
        text = "".join(c for c in text if 32 <= ord(c) < 0xFFFF and c.isprintable() and c not in '\u200b\u200c\u200d')
        if not text.strip():
            logger.debug("sanitize_text produced empty text after sanitization, returning 'N/A'")
            return "N/A"
        logger.debug(f"sanitize_text processed text: {text!r}")
        return text
    except Exception as e:
        logger.error(f"sanitize_text failed: {str(e)}, returning 'N/A'")
        return "N/A"

def generate_pdf_report(call_data):
    try:
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=20)  # Increased margin

        for i, call in enumerate(call_data):
            logger.debug(f"Processing call #{i+1}: {call!r}")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 14)  # Changed to Helvetica
            report_title = sanitize_text(f"Call Analysis Report #{i+1}")
            logger.debug(f"Rendering title: {report_title!r}")
            pdf.cell(0, 10, report_title, ln=True)

            pdf.set_font("Helvetica", "", 12)
            filename = sanitize_text(f"Filename: {call.get('filename', 'Unknown')}")
            logger.debug(f"Rendering filename: {filename!r}")
            pdf.cell(0, 10, filename, ln=True)  # Use cell for simpler rendering

            sentiment = sanitize_text(f"Sentiment: {call.get('sentiment', 'Unknown')}")
            logger.debug(f"Rendering sentiment: {sentiment!r}")
            pdf.cell(0, 10, sentiment, ln=True)  # Use cell instead of multi_cell

            call_type = sanitize_text(f"Call Type: {call.get('call_type', 'Unknown')}")
            logger.debug(f"Rendering call_type: {call_type!r}")
            pdf.cell(0, 10, call_type, ln=True)
            pdf.ln()

            pdf.set_font("Helvetica", "B", 12)
            keywords_title = sanitize_text("Keywords Detected:")
            logger.debug(f"Rendering keywords title: {keywords_title!r}")
            pdf.cell(0, 10, keywords_title, ln=True)
            pdf.set_font("Helvetica", "", 12)
            keywords = call.get("keywords", [])
            if keywords:
                for kw in keywords:
                    kw_text = sanitize_text(f"- {kw}")
                    logger.debug(f"Rendering keyword: {kw_text!r}")
                    pdf.cell(0, 8, kw_text, ln=True)
            else:
                none_text = sanitize_text("None")
                logger.debug(f"Rendering none keywords: {none_text!r}")
                pdf.cell(0, 8, none_text, ln=True)

            pdf.ln()
            pdf.set_font("Helvetica", "B", 12)
            qa_scores_title = sanitize_text("QA Scores:")
            logger.debug(f"Rendering QA scores title: {qa_scores_title!r}")
            pdf.cell(0, 10, qa_scores_title, ln=True)
            pdf.set_font("Helvetica", "", 12)
            qa_scores = call.get("qa_scores", {})
            for section, result in qa_scores.items():
                score_text = sanitize_text(f"- {section}: {result.get('score', 'N/A')} — {result.get('explanation', 'N/A')}")
                logger.debug(f"Rendering QA score: {score_text!r}")
                pdf.cell(0, 8, score_text, ln=True)

            pdf.ln()
            pdf.set_font("Helvetica", "B", 12)
            transcript_title = sanitize_text("Transcript:")
            logger.debug(f"Rendering transcript title: {transcript_title!r}")
            pdf.cell(0, 10, transcript_title, ln=True)
            pdf.set_font("Helvetica", "", 11)
            transcript = sanitize_text(call.get("transcript", "No transcript available"))
            logger.debug(f"Rendering transcript: {transcript!r}")
            pdf.multi_cell(0, 8, transcript)  # Keep multi_cell for transcript due to length

        return pdf.output(dest="S")  # Return bytes
    except Exception as e:
        logger.error(f"PDF generation failed: {str(e)}")
        # Create a fallback PDF with error message
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Helvetica", "", 12)
        pdf.multi_cell(0, 10, f"Error generating PDF: {str(e)}\nCall data: {call_data!r}")
        return pdf.output(dest="S")

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

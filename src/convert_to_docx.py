"""
Convert docs to docx
"""
import os
import logging
import pdfplumber
from docx import Document

# Get logger for this module
logger = logging.getLogger('EmailReader.DocConverter')


def convert_txt_to_docx(paragraph: str, docx_file_path: str) -> None:
    """
    Converts a plain text file to a Word document. test

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.debug("Entering convert_txt_to_docx()")
    logger.debug("Output path: %s", docx_file_path)

    try:
        text_length = len(paragraph)
        logger.debug("Text length: %d characters", text_length)

        if text_length == 0:
            logger.warning("Empty text provided for conversion")

        # Enhanced logging: Check for formatting markers that will be lost
        column_breaks = paragraph.count('[Column Break]')
        page_breaks = paragraph.count('--- Page Break ---')

        if column_breaks > 0 or page_breaks > 0:
            logger.warning(
                "FORMATTING LOSS WARNING: Using basic single-paragraph conversion method. "
                f"Found {column_breaks} column break markers and {page_breaks} page break markers "
                "that will be preserved as plain text instead of actual formatting. "
                "Consider using convert_structured_to_docx() for full formatting preservation."
            )

        logger.info("Using basic DOCX conversion (single paragraph, no structural formatting)")
        logger.debug("Creating new Word document")
        document = Document()
        document.add_paragraph(paragraph)

        logger.debug("Saving document to: %s", docx_file_path)
        document.save(docx_file_path)

        if os.path.exists(docx_file_path):
            file_size = os.path.getsize(docx_file_path) / 1024  # KB
            logger.info('Text converted to Word successfully: %s (%.2f KB)',
                       os.path.basename(docx_file_path), file_size)
        else:
            logger.error("Document save failed - file not found: %s", docx_file_path)

    except Exception as e:
        logger.error("Error converting text to DOCX: %s", e, exc_info=True)
        raise


def convert_txt_file_to_docx(txt_file_path: str, docx_file_path: str) -> None:
    """
    Converts a plain text file to a Word document.

    Args:
        paragraph: text.
        docx_file_path: Path to save the output Word document.
    """
    logger.debug("Entering convert_txt_file_to_docx()")
    logger.debug("Input TXT: %s", txt_file_path)
    logger.debug("Output DOCX: %s", docx_file_path)

    try:
        if not os.path.exists(txt_file_path):
            logger.error("Text file not found: %s", txt_file_path)
            raise FileNotFoundError(f"File not found: {txt_file_path}")

        input_size = os.path.getsize(txt_file_path) / 1024  # KB
        logger.debug("Input file size: %.2f KB", input_size)

        logger.debug("Reading text file")
        with open(txt_file_path, 'r', encoding='utf-8') as file:
            paragraph = file.read()

        text_length = len(paragraph)
        logger.debug("Read %d characters from file", text_length)

        logger.debug("Creating Word document")
        document = Document()
        document.add_paragraph(paragraph)

        logger.debug("Saving document to: %s", docx_file_path)
        document.save(docx_file_path)

        if os.path.exists(docx_file_path):
            output_size = os.path.getsize(docx_file_path) / 1024  # KB
            logger.info('TXT file converted to Word: %s (%.2f KB)',
                       os.path.basename(docx_file_path), output_size)
        else:
            logger.error("Document save failed - file not found: %s", docx_file_path)

    except Exception as e:
        logger.error("Error converting TXT file to DOCX: %s", e, exc_info=True)
        raise


def convert_pdf_to_docx(pdf_path: str, docx_path: str):
    """
    Converts a PDF file to a DOCX file, preserving text formatting.
    """
    logger.debug("Entering convert_pdf_to_docx()")
    logger.debug("Input PDF: %s", pdf_path)
    logger.debug("Output DOCX: %s", docx_path)

    try:
        if not os.path.exists(pdf_path):
            logger.error("PDF file not found: %s", pdf_path)
            raise FileNotFoundError(f"File not found: {pdf_path}")

        input_size = os.path.getsize(pdf_path) / 1024  # KB
        logger.debug("Input PDF size: %.2f KB", input_size)

        logger.debug("Opening PDF with pdfplumber")
        document = Document()
        total_text_length = 0

        with pdfplumber.open(pdf_path) as pdf:
            num_pages = len(pdf.pages)
            logger.info("PDF has %d pages", num_pages)

            for page_num, page in enumerate(pdf.pages, 1):
                logger.debug("Processing page %d/%d", page_num, num_pages)
                text = page.extract_text()

                if text:
                    text_length = len(text)
                    total_text_length += text_length
                    logger.debug("Page %d: extracted %d characters", page_num, text_length)
                    document.add_paragraph(text)
                else:
                    logger.debug("Page %d: no text extracted", page_num)

            logger.info("Total text extracted: %d characters from %d pages",
                       total_text_length, num_pages)

            logger.debug("Saving DOCX file")
            document.save(docx_path)

        if os.path.exists(docx_path):
            output_size = os.path.getsize(docx_path) / 1024  # KB
            logger.info('PDF converted to Word: %s (%.2f KB)',
                       os.path.basename(docx_path), output_size)
        else:
            logger.error("Document save failed - file not found: %s", docx_path)

    except Exception as e:
        logger.error("Error converting PDF to DOCX: %s", e, exc_info=True)
        raise


def convert_structured_to_docx(formatted_doc: 'FormattedDocument', output_path: str) -> None:
    """
    Convert a FormattedDocument to DOCX with full formatting preservation.

    This function preserves:
    - Page breaks (actual page breaks, not text markers)
    - Column layout (using section-based columns)
    - Paragraph spacing (based on vertical gaps)
    - Font sizes (inferred from bounding box heights)

    Args:
        formatted_doc: FormattedDocument instance with structured formatting data
        output_path: Path where DOCX file should be saved

    Raises:
        ValueError: If formatted_doc is invalid
        RuntimeError: If DOCX creation fails
    """
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
    from src.models.formatted_document import FormattedDocument

    logger.info("Using ADVANCED DOCX conversion (full formatting preservation)")
    logger.debug(f"Output path: {output_path}")
    logger.debug(f"Document has {formatted_doc.total_pages} pages, {formatted_doc.total_paragraphs} paragraphs")

    if not isinstance(formatted_doc, FormattedDocument):
        raise ValueError("formatted_doc must be a FormattedDocument instance")

    if formatted_doc.total_pages == 0:
        logger.warning("No pages in formatted document, creating empty DOCX")

    try:
        document = Document()
        total_paragraphs_written = 0

        for page_idx, page in enumerate(formatted_doc.pages):
            logger.debug(f"Processing page {page.page_number + 1}/{formatted_doc.total_pages} "
                        f"({len(page.paragraphs)} paragraphs, {page.columns} columns)")

            # Add page break before new pages (not for first page)
            if page_idx > 0:
                # Insert an explicit page break before this page's content
                break_para = document.add_paragraph()
                break_para.add_run().add_break(WD_BREAK.PAGE)
                logger.debug(f"Inserted explicit page break before page {page.page_number + 1}")

            needs_page_break = False  # Already handled above

            # Handle multi-column layout
            if page.columns > 1:
                # Create a new section for this page with columns
                section = document.add_section()

                # Set number of columns (python-docx doesn't have direct column support,
                # so we'll use a table-based approach for now)
                logger.debug(f"Page {page.page_number + 1} has {page.columns} columns - using table layout")

                # Group paragraphs by column
                columns_data = {}
                for para in page.paragraphs:
                    col = para.column
                    if col not in columns_data:
                        columns_data[col] = []
                    columns_data[col].append(para)

                # Create table for columns
                table = document.add_table(rows=1, cols=page.columns)
                table.autofit = False
                table.allow_autofit = False

                # Populate columns
                for col_num in range(page.columns):
                    cell = table.rows[0].cells[col_num]
                    cell_paragraphs = columns_data.get(col_num, [])

                    # Clear default paragraph
                    if cell.paragraphs:
                        cell.paragraphs[0].text = ''

                    for para_idx, para in enumerate(cell_paragraphs):
                        # Create empty paragraph first, then add run with formatting
                        p = cell.add_paragraph()
                        run = p.add_run(para.text)

                        # Apply font formatting using inferred font size
                        run.font.name = 'Times New Roman'
                        if para.font_size is not None:
                            run.font.size = Pt(para.font_size)
                            logger.debug(f"Applied font size: {para.font_size}pt")
                        else:
                            run.font.size = Pt(12)  # Default fallback
                        run.font.bold = para.is_bold
                        run.font.italic = para.is_italic

                        # Add page break on first paragraph of new page
                        if needs_page_break and col_num == 0 and para_idx == 0:
                            p.paragraph_format.page_break_before = True
                            logger.debug(f"Added page_break_before on page {page.page_number + 1} (table)")
                            needs_page_break = False

                        # Apply vertical spacing
                        if para.vertical_gap_before > 0.05:  # Significant gap
                            p.paragraph_format.space_before = Pt(para.vertical_gap_before * 200)

                        total_paragraphs_written += 1

                logger.debug(f"Created {page.columns}-column table with {len(page.paragraphs)} paragraphs")

            else:
                # Single column - add paragraphs normally
                previous_para_bottom = None

                for para_idx, para in enumerate(page.paragraphs):
                    # Create empty paragraph first, then add run with formatting
                    p = document.add_paragraph()
                    run = p.add_run(para.text)

                    # Apply font formatting using inferred font size
                    run.font.name = 'Times New Roman'
                    if para.font_size is not None:
                        run.font.size = Pt(para.font_size)
                        logger.debug(f"Applied font size: {para.font_size}pt (type: {para.text_type})")
                    else:
                        run.font.size = Pt(12)  # Default fallback
                        logger.debug("Applied default 12pt font size")
                    run.font.bold = para.is_bold
                    run.font.italic = para.is_italic

                    # Add page break on first paragraph of new page
                    if needs_page_break and para_idx == 0:
                        p.paragraph_format.page_break_before = True
                        logger.debug(f"Added page_break_before on page {page.page_number + 1}")
                        needs_page_break = False

                    # Calculate vertical spacing from previous paragraph
                    if previous_para_bottom is not None:
                        gap = para.position.top - previous_para_bottom
                        if gap > 0.05:  # Significant gap (5% of page height)
                            space_before = Pt(gap * 200)  # Convert to points
                            p.paragraph_format.space_before = space_before
                            logger.debug(f"Added vertical spacing: {gap:.3f} normalized ({space_before.pt:.1f}pt)")

                    previous_para_bottom = para.position.bottom
                    total_paragraphs_written += 1

        # Save document
        logger.debug(f"Saving DOCX with {total_paragraphs_written} paragraphs")
        document.save(output_path)

        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path) / 1024  # KB
            logger.info(
                f"Structured document converted to DOCX: {os.path.basename(output_path)} "
                f"({file_size:.2f} KB, {total_paragraphs_written} paragraphs, "
                f"{formatted_doc.total_pages} pages)"
            )
        else:
            logger.error(f"DOCX save failed - file not found: {output_path}")
            raise RuntimeError(f"Failed to save DOCX file: {output_path}")

    except Exception as e:
        logger.error(f"Error converting structured document to DOCX: {e}", exc_info=True)
        raise RuntimeError(f"Structured DOCX conversion failed: {e}") from e

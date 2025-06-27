import os
import re
import sys
from pathlib import Path
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


def create_header_footer_page(filename):
    """Creates a PDF page with the filename as header and footer."""
    import io  # Import here, only needed in this function
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    can.setFont('Helvetica', 12)

    # Header
    can.drawString(50, 750, filename)  # Adjust coordinates as needed

    # Footer
    can.drawString(50, 50, filename)  # Adjust coordinates as needed

    can.save()

    # move to the beginning of the buffer
    packet.seek(0)
    new_pdf = PdfReader(packet)
    return new_pdf.pages[0]


def combine_pdfs_with_toc(input_dir, output_file):
    """
    Combines PDFs from a directory into a single PDF with a table of contents,
    header/trailer pages for each document.
    """
    import io  # Import here, only needed in this function

    pdf_files = sorted([
        f for f in os.listdir(input_dir)
        if f.lower().endswith(".pdf")
    ])

    if not pdf_files:
        print("No PDF files found in the input directory.")
        return

    output_pdf = PdfWriter()
    toc = []  # List to store Table of Contents entries

    # Create ToC page
    toc_page = io.BytesIO()
    toc_canvas = canvas.Canvas(toc_page, pagesize=letter)
    toc_canvas.setFont('Helvetica', 12)
    toc_title = "Table of Contents"
    toc_canvas.setFontSize(16) #Larger title
    toc_canvas.drawCentredString(letter[0] / 2.0, 750, toc_title) # centered
    toc_canvas.setFontSize(12) # back to normal
    toc_canvas.save()
    toc_page.seek(0)
    toc_pdf = PdfReader(toc_page)
    toc_first_page = toc_pdf.pages[0]
    #output_pdf.add_page(toc_first_page) # Add empty ToC first page - NO LONGER NEEDED. Moved insert_page

    page_number = 0 #Keep current number - CHANGED START VALUE

    # Process each PDF file
    for pdf_file in pdf_files:
        input_path = os.path.join(input_dir, pdf_file)
        filename_without_extension = Path(pdf_file).stem  # Remove .pdf

        # Add ToC entry
        toc.append((filename_without_extension, page_number+2)) # plus 2 because of cover and header

        # Create header/footer page
        header_footer = create_header_footer_page(filename_without_extension)

        # Process the PDF
        with open(input_path, "rb") as f:
            pdf_reader = PdfReader(f)
            #header page
            output_pdf.add_page(header_footer)
            page_number +=1
            #Content pages
            for page in pdf_reader.pages:
                output_pdf.add_page(page)
                page_number += 1
            #trailer page
            output_pdf.add_page(header_footer)
            page_number +=1


    # Generate ToC content, now that we know the page numbers:
    toc_page = io.BytesIO()
    toc_canvas = canvas.Canvas(toc_page, pagesize=letter)
    toc_canvas.setFont('Helvetica', 12)
    toc_title = "Table of Contents"
    toc_canvas.setFontSize(16) #Larger title
    toc_canvas.drawCentredString(letter[0] / 2.0, 750, toc_title) # centered
    toc_canvas.setFontSize(12) # back to normal

    y_position = 700  # Starting Y position for ToC entries
    line_height = 14 # adjust as required
    left_margin = 75 #adjust as required
    for title, page_num in toc:
        toc_canvas.drawString(left_margin, y_position, f"{title} - Page {page_num}")
        y_position -= line_height
        if y_position < 100: # check for page overflow, if necessary. Not implemented to reduce requirements
            print ("error, toc is bigger than one page. implement pagination here if required")
            sys.exit()

    toc_canvas.save()
    toc_page.seek(0)
    toc_pdf = PdfReader(toc_page)
    toc_first_page = toc_pdf.pages[0]

    #Insert table of contents at the beginning
    output_pdf.insert_page(toc_first_page, index=0)  # Insert ToC at the beginning

    # Save the combined PDF
    with open(output_file, "wb") as output_f:
        output_pdf.write(output_f)

    print(f"Successfully combined PDFs into '{output_file}'")


if __name__ == "__main__":
    import io  #Move import inside if __name__ block, per best practices (MOVED IMPORT TO OTHER FUNCTIONS)

    if len(sys.argv) != 3:
        print("Usage: python combine_pdfs.py <input_directory> <output_file>")
        sys.exit(1)

    input_directory = sys.argv[1]
    output_filename = sys.argv[2]

    combine_pdfs_with_toc(input_directory, output_filename)
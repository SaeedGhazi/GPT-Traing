import os
import sys
import re
import tabula
import pandas as pd
import nltk
import argparse
import csv
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTChar, LTTextLine

# Download NLTK data files (only needs to be done once)
nltk.download('punkt', quiet=True)

def extract_text_with_layout(pdf_path):
    content = []
    current_paragraph = ''
    prev_size = None  # Initialize previous font size
    in_toc = False  # Flag to indicate we're in the TOC section
    toc_entries = []

    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                for text_line in element:
                    if isinstance(text_line, LTTextLine):
                        text = text_line.get_text().strip()
                        if not text:
                            continue

                        # Skip headers and footers if necessary
                        if is_header_or_footer(text):
                            continue

                        # Check if we've reached the "FOREWORD" page to end TOC collection
                        if re.match(r'^FOREWORD$', text, re.IGNORECASE):
                            in_toc = False

                        # Check if we're in the TOC section
                        if in_toc:
                            # Clean TOC line
                            toc_title = clean_toc_line(text)
                            if toc_title:
                                toc_entries.append(toc_title)
                            continue  # Skip further processing for TOC lines

                        # Check if we're at the start of the TOC
                        if re.match(r'^TABLE OF CONTENTS$', text, re.IGNORECASE):
                            in_toc = True
                            continue  # Skip the "TABLE OF CONTENTS" heading

                        # Get average font size
                        font_sizes = [char.size for char in text_line if isinstance(char, LTChar)]
                        avg_font_size = sum(font_sizes) / len(font_sizes) if font_sizes else 0

                        # Determine heading level based on text patterns and font size
                        heading_level = determine_heading_level(text_line, avg_font_size, prev_size)
                        if heading_level:
                            # Save current paragraph
                            if current_paragraph:
                                content.append(('paragraph', current_paragraph.strip()))
                                current_paragraph = ''
                            # Add heading
                            content.append(('heading', text.strip(), heading_level))
                            prev_size = avg_font_size
                            continue

                        # Joining logic
                        if current_paragraph:
                            if should_join_lines(current_paragraph, text):
                                if current_paragraph.endswith('-'):
                                    # Remove hyphen and join words
                                    current_paragraph = current_paragraph[:-1] + text
                                else:
                                    current_paragraph += ' ' + text
                            else:
                                # Save current paragraph and start a new one
                                content.append(('paragraph', current_paragraph.strip()))
                                current_paragraph = text
                        else:
                            current_paragraph = text

                        prev_size = avg_font_size  # Update previous font size

                    elif isinstance(text_line, LTChar):
                        # Handle LTChar instances separately
                        text = text_line.get_text().strip()
                        if not text:
                            continue

                        # Get font size
                        avg_font_size = text_line.size

                        # Process the text as needed
                        # For simplicity, we'll treat it as a paragraph
                        current_paragraph += text

                        prev_size = avg_font_size  # Update previous font size

                    else:
                        # Skip other types
                        continue

    # Append any remaining paragraph
    if current_paragraph:
        content.append(('paragraph', current_paragraph.strip()))

    return content, toc_entries

def clean_toc_line(text):
    # Remove dots and page numbers from TOC lines
    text = text.strip()
    text = re.sub(r'\.{2,}', '', text)
    text = re.sub(r'\s+\d+(-\d+)?$', '', text)
    if not text:
        return None
    return text

def is_header_or_footer(text):
    text = text.strip().lower()
    if re.match(r'^\d+$', text):  # Page numbers
        return True
    if 'confidential' in text:
        return True
    if 'icao' in text:
        return True
    return False

def determine_heading_level(text_line, avg_font_size, prev_font_size):
    # Extract the text from the text_line
    if isinstance(text_line, LTTextLine):
        text = text_line.get_text().strip()
    elif isinstance(text_line, str):
        text = text_line.strip()
    else:
        return None

    # Check for 'Chapter' heading
    if re.match(r'^Chapter\s+\d+', text, re.IGNORECASE):
        return '#'  # Level 1 heading

    # Check for all caps headings (likely top-level headings)
    elif re.match(r'^[A-Z ]+$', text) and len(text.split()) < 10:
        return '#'  # Level 1 heading

    else:
        # Match numeric headings like '4.3.2' at the beginning of the text
        match = re.match(r'^((\d+\.)+\d+)', text)
        if match:
            heading_number = match.group(1)  # The matched heading number
            segments = heading_number.split('.')
            level = len(segments)
            if level > 6:
                level = 6  # Limit to maximum 6 levels
            return '#' * level

    # Compare font size to detect headings
    if avg_font_size and prev_font_size:
        if avg_font_size > prev_font_size * 1.2:
            # If current font size is significantly larger than previous, it might be a heading
            level = determine_level_by_font_size(avg_font_size)
            return '#' * level

    # Check for bold text
    if is_bold_text(text_line):
        return '##'  # Assign Level 2 heading as an example

    return None  # Not a heading

def determine_level_by_font_size(font_size):
    # You may need to adjust these thresholds based on your PDFs
    if font_size >= 20:
        return 1  # Level 1 heading
    elif font_size >= 18:
        return 2  # Level 2 heading
    elif font_size >= 16:
        return 3  # Level 3 heading
    elif font_size >= 14:
        return 4  # Level 4 heading
    elif font_size >= 12:
        return 5  # Level 5 heading
    else:
        return 6  # Level 6 heading

def is_bold_text(text_line):
    if isinstance(text_line, LTTextLine):
        for char in text_line:
            if isinstance(char, LTChar) and 'Bold' in char.fontname:
                return True
    return False

def should_join_lines(prev_line, current_line):
    if prev_line.endswith('-'):
        return True
    if not re.search(r'[.!?]"?$', prev_line):
        return True
    if current_line and current_line[0].islower():
        return True
    if re.match(r'^\d+(\.\d+)*\s', current_line):
        return False
    if re.match(r'^[A-Z][A-Z ]+$', current_line):
        return False
    return False

def extract_tables(pdf_path, pages='all'):
    try:
        dfs = tabula.read_pdf(pdf_path, pages=pages, multiple_tables=True)
        return dfs
    except Exception as e:
        print(f"Error extracting tables: {e}")
        return []

def tables_to_markdown(dfs):
    markdown_tables = []
    for df in dfs:
        df = df.replace('\r', ' ', regex=True)
        df = df.fillna('')  # Replace NaN with empty string
        md_table = df.to_markdown(index=False)
        markdown_tables.append(md_table)
    return markdown_tables

def combine_content(content_list, toc_entries, markdown_tables, metadata):
    markdown_content = ''

    # Include book metadata
    if metadata:
        markdown_content += f"# {metadata.get('book_name', 'Untitled')}\n\n"
        markdown_content += f"**Document Number:** {metadata.get('doc_number', 'N/A')}\n\n"
        markdown_content += f"**Organization:** {metadata.get('organization', 'N/A')}\n\n"
        markdown_content += f"**Revision Date:** {metadata.get('revision_date', 'N/A')}\n\n"
        markdown_content += f"**Edition:** {metadata.get('edition', 'N/A')}\n\n"

    # Include the Table of Contents
    if toc_entries:
        markdown_content += '## Table of Contents\n\n'
        for entry in toc_entries:
            markdown_content += f'- {entry}\n'
        markdown_content += '\n'

    table_index = 0

    for idx, item in enumerate(content_list):
        if item[0] == 'heading':
            _, text, heading_level = item
            markdown_content += f'\n{heading_level} {text}\n\n'
            if 'table' in text.lower() and table_index < len(markdown_tables):
                markdown_content += f'{markdown_tables[table_index]}\n\n'
                table_index += 1
        elif item[0] == 'paragraph':
            _, text = item
            sentences = nltk.tokenize.sent_tokenize(text)
            for sentence in sentences:
                markdown_content += f'{sentence}\n\n'
        else:
            pass

    return markdown_content

def extract_existing_books(markdown_content):
    pattern = (
        r'^#\s+(.*?)\n+'
        r'\*\*Document Number:\*\*\s*(.*?)\n+'
        r'\*\*Organization:\*\*\s*(.*?)\n+'
        r'\*\*Revision Date:\*\*\s*(.*?)\n+'
        r'\*\*Edition:\*\*\s*(.*?)\n+'
    )
    matches = re.findall(pattern, markdown_content, flags=re.MULTILINE | re.IGNORECASE)
    existing_books = []
    for match in matches:
        book_name = match[0].strip()
        doc_number = match[1].strip()
        organization = match[2].strip()
        revision_date = match[3].strip()
        edition = match[4].strip()
        existing_books.append({
            'book_name': book_name.lower(),
            'doc_number': doc_number.lower(),
            'organization': organization.lower(),
            'revision_date': revision_date.lower(),
            'edition': edition.lower()
        })
    return existing_books

def list_books_in_markdown(markdown_content):
    existing_books = extract_existing_books(markdown_content)
    if existing_books:
        print("Books currently in the Markdown file:")
        for book in existing_books:
            print(f"- {book['book_name']} (Document Number: {book['doc_number']}, Organization: {book['organization']}, Revision Date: {book['revision_date']}, Edition: {book['edition']})")
    else:
        print("No books found in the Markdown file.")

def read_metadata_csv(csv_file_path):
    metadata_list = []
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            required_fields = {'pdf_path', 'book_name', 'doc_number', 'organization', 'revision_date', 'edition'}
            if not required_fields.issubset(reader.fieldnames):
                print(f"CSV file must contain the following columns: {', '.join(required_fields)}")
                sys.exit(1)
            for row in reader:
                metadata_list.append({
                    'pdf_path': row['pdf_path'],
                    'book_name': row['book_name'],
                    'doc_number': row['doc_number'],
                    'organization': row['organization'],
                    'revision_date': row['revision_date'],
                    'edition': row['edition']
                })
    except Exception as e:
        print(f"Error reading CSV file: {e}")
        sys.exit(1)
    return metadata_list

def main():
    parser = argparse.ArgumentParser(
        description='''Convert PDF files to a combined Markdown document with optional metadata and duplicate checking.

You can provide metadata via command-line arguments or a CSV file. If both are provided, the CSV file will be used.

Example usage:
  python pdf_to_markdown.py --output combined_output.md --metadata-csv metadata.csv
  python pdf_to_markdown.py --output combined_output.md --book-name "Book Title" --doc-number "Doc No. 123" --organization "Organization Name" --revision-date "2023-10-15" --edition "Second Edition" file.pdf
''',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument('--output', '-o', type=str, required=True, help='Output Markdown file path.')
    parser.add_argument('--book-name', nargs='*', type=str, help='Book name/title(s).')
    parser.add_argument('--doc-number', nargs='*', type=str, help='Document number(s).')
    parser.add_argument('--organization', nargs='*', type=str, help='Organization(s)/Publication(s).')
    parser.add_argument('--revision-date', nargs='*', type=str, help='Revision date(s) (e.g., "2023-10-15").')
    parser.add_argument('--edition', nargs='*', type=str, help='Edition(s) (e.g., "First Edition").')
    parser.add_argument('--metadata-csv', type=str, help='Path to CSV file containing metadata.')
    parser.add_argument('--list-books', action='store_true', help='List books currently in the Markdown file and exit.')
    parser.add_argument('pdf_paths', nargs='*', help='Paths to PDF files.')

    args = parser.parse_args()

    # Read existing content if the output file exists
    if os.path.exists(args.output):
        with open(args.output, 'r', encoding='utf-8') as f:
            combined_markdown = f.read()
        existing_books = extract_existing_books(combined_markdown)
    else:
        combined_markdown = ''
        existing_books = []

    # If --list-books is specified, list the books and exit
    if args.list_books:
        list_books_in_markdown(combined_markdown)
        sys.exit(0)

    metadata_list = []

    if args.metadata_csv:
        # Read metadata from CSV file
        metadata_list = read_metadata_csv(args.metadata_csv)
    else:
        if not args.pdf_paths:
            print("No PDF files specified.")
            sys.exit(1)

        num_pdfs = len(args.pdf_paths)

        # Ensure metadata lists match the number of PDFs
        book_names = args.book_name if args.book_name else [None] * num_pdfs
        doc_numbers = args.doc_number if args.doc_number else [None] * num_pdfs
        organizations = args.organization if args.organization else [None] * num_pdfs
        revision_dates = args.revision_date if args.revision_date else [None] * num_pdfs
        editions = args.edition if args.edition else [None] * num_pdfs

        # If only one metadata value is provided, use it for all PDFs
        if len(book_names) == 1 and num_pdfs > 1:
            book_names = book_names * num_pdfs
        if len(doc_numbers) == 1 and num_pdfs > 1:
            doc_numbers = doc_numbers * num_pdfs
        if len(organizations) == 1 and num_pdfs > 1:
            organizations = organizations * num_pdfs
        if len(revision_dates) == 1 and num_pdfs > 1:
            revision_dates = revision_dates * num_pdfs
        if len(editions) == 1 and num_pdfs > 1:
            editions = editions * num_pdfs

        # Check if the number of metadata values matches the number of PDFs
        if not (len(book_names) == len(doc_numbers) == len(organizations) == len(revision_dates) == len(editions) == num_pdfs):
            print("Error: The number of metadata values must match the number of PDF files.")
            sys.exit(1)

        for idx, pdf_path in enumerate(args.pdf_paths):
            book_name = book_names[idx] or os.path.splitext(os.path.basename(pdf_path))[0]
            doc_number = doc_numbers[idx] or 'N/A'
            organization = organizations[idx] or 'N/A'
            revision_date = revision_dates[idx] or 'N/A'
            edition = editions[idx] or 'N/A'
            metadata_list.append({
                'pdf_path': pdf_path,
                'book_name': book_name,
                'doc_number': doc_number,
                'organization': organization,
                'revision_date': revision_date,
                'edition': edition
            })

    for metadata in metadata_list:
        pdf_path = metadata['pdf_path']
        book_name = metadata['book_name']
        doc_number = metadata['doc_number']
        organization = metadata['organization']
        revision_date = metadata['revision_date']
        edition = metadata['edition']

        # Check if the book is already in the Markdown file (case-insensitive)
        is_duplicate = False
        for existing_book in existing_books:
            if (existing_book['book_name'] == book_name.lower() and
                existing_book['doc_number'] == doc_number.lower() and
                existing_book['organization'] == organization.lower() and
                existing_book['revision_date'] == revision_date.lower() and
                existing_book['edition'] == edition.lower()):
                is_duplicate = True
                break

        if is_duplicate:
            print(f"Skipping '{book_name}' as it is already present in the Markdown file.")
            continue  # Skip processing this PDF

        if not os.path.exists(pdf_path):
            print(f"PDF file not found: {pdf_path}")
            continue

        print(f"Processing '{book_name}'...")

        try:
            # Extract content
            content_list, toc_entries = extract_text_with_layout(pdf_path)

            # Extract tables
            dfs = extract_tables(pdf_path)
            markdown_tables = tables_to_markdown(dfs)

            # Combine content into Markdown format
            markdown_content = combine_content(content_list, toc_entries, markdown_tables, metadata)

            # Append to combined Markdown content with separator
            combined_markdown = markdown_content + '\n\n---\n\n'  # Separator between books

            # Write the combined Markdown content to the output file after each PDF
            with open(args.output, 'a', encoding='utf-8') as f:
                f.write(combined_markdown)

            # Add the book to the list of existing books
            existing_books.append({
                'book_name': book_name.lower(),
                'doc_number': doc_number.lower(),
                'organization': organization.lower(),
                'revision_date': revision_date.lower(),
                'edition': edition.lower()
            })

        except Exception as e:
            print(f"Error processing '{book_name}': {e}")
            continue  # Skip to the next PDF

if __name__ == '__main__':
    main()

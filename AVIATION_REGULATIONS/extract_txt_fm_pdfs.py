import PyPDF2
import re
import os
import shutil

def extract_text_from_pdfs(directory):
    # Create the Processed folder if it doesn't exist
    processed_folder = os.path.join(directory, 'Processed')
    os.makedirs(processed_folder, exist_ok=True)

    # Define the output text file path
    output_txt = os.path.join(processed_folder, 'extracted_text.txt')

    # Loop through all PDF files in the directory
    for filename in os.listdir(directory):
        if filename.lower().endswith('.pdf'):
            pdf_path = os.path.join(directory, filename)
            process_pdf(pdf_path, output_txt)
            
            # Move the processed PDF to the Processed folder
            shutil.move(pdf_path, os.path.join(processed_folder, filename))

def process_pdf(pdf_path, output_txt):
    # Open the PDF file
    with open(pdf_path, 'rb') as file:
        # Create a PDF reader
        reader = PyPDF2.PdfReader(file)
        # Get the name of the document
        doc_name = os.path.basename(pdf_path)
        
        # Open the output text file in append mode
        with open(output_txt, 'a', encoding='utf-8') as output_file:
            # Write the separator with document name
            output_file.write(f"**** {doc_name} ****\n")
            
            # Iterate through pages and extract text
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text = page.extract_text()
                
                # Process section numbers and titles
                processed_text = process_text(text)
                
                # Write the processed text to the output file
                output_file.write(processed_text)
                output_file.write("\n")
            
            # Write the end separator
            output_file.write(f"**** END OF {doc_name} ****\n\n")

def process_text(text):
    # Regex to match section numbers in the format n1.n2.n3...nn
    section_pattern = re.compile(r'\b\d+(\.\d+)+\b')
    
    lines = text.splitlines()
    processed_lines = []
    current_section = None
    
    for line in lines:
        # Strip leading and trailing whitespace
        line = line.strip()
        
        # Skip empty lines
        if not line:
            continue
        
        # Check if the line starts with a section number
        section_match = section_pattern.match(line)
        if section_match:
            # Save the current section number
            current_section = section_match.group()
            # Append section number to processed_lines
            processed_lines.append(f"\n### Section {current_section} ###\n")
        
        # Remove unnecessary newlines within paragraphs
        if current_section and not line.isupper():
            line = re.sub(r'\n(?!\n)', ' ', line)
        
        processed_lines.append(line)
    
    return "\n".join(processed_lines)

# Usage example
directory = '.'
extract_text_from_pdfs(directory)

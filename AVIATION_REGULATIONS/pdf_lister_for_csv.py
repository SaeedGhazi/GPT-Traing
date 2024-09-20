import os
import sys
import csv
import argparse

def generate_metadata_csv(pdf_folder, output_csv='metadata.csv'):
  # List to store metadata dictionaries
  metadata_list = []

  # Walk through the folder and find all PDF files
  for root, dirs, files in os.walk(pdf_folder):
      for file in files:
          if file.lower().endswith('.pdf'):
              pdf_path = os.path.join(root, file)
              # Use default metadata values
              metadata = {
                  'pdf_path': pdf_path,
                  'book_name': os.path.splitext(file)[0],  # Default book name is the file name without extension
                  'doc_number': 'N/A',
                  'organization': 'N/A',
                  'revision_date': 'N/A',
                  'edition': 'N/A'
              }
              metadata_list.append(metadata)

  if not metadata_list:
      print(f"No PDF files found in the folder: {pdf_folder}")
      sys.exit(1)

  # Write the metadata to a CSV file
  fieldnames = ['pdf_path', 'book_name', 'doc_number', 'organization', 'revision_date', 'edition']
  try:
      with open(output_csv, 'w', encoding='utf-8', newline='') as csvfile:
          writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
          writer.writeheader()
          for metadata in metadata_list:
              writer.writerow(metadata)
      print(f"Metadata CSV file '{output_csv}' has been created.")
      print("Please update the 'book_name', 'doc_number', 'organization', 'revision_date', and 'edition' columns as needed.")
  except Exception as e:
      print(f"Error writing CSV file: {e}")
      sys.exit(1)

def main():
  parser = argparse.ArgumentParser(description='Generate a metadata CSV file for PDFs in a folder.')
  parser.add_argument('--pdf-folder', '-p', type=str, required=True, help='Path to the folder containing PDF files.')
  parser.add_argument('--output-csv', '-o', type=str, default='metadata.csv', help='Output CSV file name (default: metadata.csv).')

  args = parser.parse_args()

  pdf_folder = args.pdf_folder
  output_csv = args.output_csv

  if not os.path.isdir(pdf_folder):
      print(f"The specified folder does not exist: {pdf_folder}")
      sys.exit(1)

  generate_metadata_csv(pdf_folder, output_csv)

if __name__ == '__main__':
  main()

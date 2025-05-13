# processors/document_processor.py
import re
import os
import io
import json
import shutil
import tempfile
import base64
from datetime import datetime
from uuid import uuid4
import pytesseract
from PIL import Image, ImageChops
import pandas as pd
import hashlib
import numpy as np
from pdf2image import convert_from_bytes
import fitz
import streamlit as st
from openai import OpenAI

# Try importing MarkItDown
try:
    from markitdown import MarkItDown
    MARKITDOWN_AVAILABLE = True
except ImportError:
    MARKITDOWN_AVAILABLE = False

class DocumentProcessor:
    """Base class for document processing"""
    
    def process_document(self, uploaded_file):
        """Process a document based on its file type"""
        if not uploaded_file:
            return {"status": "error", "message": "No file uploaded"}
            
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        # Image files - use OCR
        if file_extension in ['png', 'jpg', 'jpeg', 'bmp', 'gif', 'tiff']:
            return self.process_image_ocr(uploaded_file)
            
        # PDF - check if it's image-based or text-based
        elif file_extension == 'pdf':
            return self.process_pdf(uploaded_file)
            
        # Other document types - use MarkItDown if available
        else:
            return self.process_with_markitdown(uploaded_file)
    
    def process_image_ocr(self, uploaded_file):
        """Process an image file with OCR"""
        try:
            image = Image.open(uploaded_file)
            extracted_text = pytesseract.image_to_string(image)
            
            # Process the OCR text to extract structured data
            invoice_data = self.extract_invoice_data(extracted_text)
            
            return {
                "status": "success",
                "method": "ocr",
                "raw_text": extracted_text,
                "structured_data": invoice_data,
                "formatted_text": extracted_text
            }
        except Exception as e:
            return {
                "status": "error",
                "method": "ocr",
                "message": f"Error processing image: {str(e)}"
            }
    
    def process_pdf(self, uploaded_file):
        """Process a PDF file with text extraction or OCR"""
        try:
            file_bytes = uploaded_file.getvalue()
            
            # First, try to extract text directly (text-based PDF)
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            extracted_text = "\n".join([page.get_text() for page in doc])
            
            # If no text extracted, it might be an image-based PDF
            if not extracted_text.strip():
                images = convert_from_bytes(file_bytes)
                extracted_text = pytesseract.image_to_string(images[0])
                method = "ocr"
            else:
                method = "text_extraction"
                
            # Process the text to extract structured data
            invoice_data = self.extract_invoice_data(extracted_text)
            
            return {
                "status": "success",
                "method": method,
                "raw_text": extracted_text,
                "structured_data": invoice_data,
                "formatted_text": extracted_text
            }
        except Exception as e:
            return {
                "status": "error",
                "method": "pdf_processing",
                "message": f"Error processing PDF: {str(e)}"
            }
    
    def process_with_markitdown(self, uploaded_file):
        """Process a file using MarkItDown and AI extraction"""
        if not MARKITDOWN_AVAILABLE:
            return {
                "status": "error",
                "method": "markitdown",
                "message": "MarkItDown library is not installed. Please install it to use this feature."
            }
        
        try:
            # Create a temporary directory
            temp_dir = tempfile.mkdtemp()
            file_path = os.path.join(temp_dir, uploaded_file.name)
            
            # Save the uploaded file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            # Convert the file to Markdown
            md = MarkItDown()
            result = md.convert(file_path)
            markdown_content = result.text_content
            
            # Call DeepSeek API to extract structured data
            api_key = st.session_state.get('deepseek_api_key', '')
            if not api_key:
                shutil.rmtree(temp_dir)
                return {
                    "status": "warning",
                    "method": "markitdown",
                    "raw_text": markdown_content,
                    "message": "DeepSeek API key not provided. Only markdown conversion is available."
                }
            
            structured_json = self._extract_with_ai(api_key, markdown_content)
            
            # Clean up
            shutil.rmtree(temp_dir)
            
            return {
                "status": "success",
                "method": "markitdown",
                "raw_text": markdown_content,
                "structured_data": structured_json['data'],
                "formatted_text": markdown_content,
                "ai_extracted_text": structured_json['raw_response']
            }
                
        except Exception as e:
            try:
                shutil.rmtree(temp_dir)
            except:
                pass
                
            return {
                "status": "error",
                "method": "markitdown",
                "message": f"Error processing with MarkItDown: {str(e)}"
            }
    
    def _extract_with_ai(self, api_key, text_content):
        """Use AI to extract structured data from text"""
        # Define attributes for extraction
        attributes = [
            "invoice_number",
            "invoice_date",
            "supplier_name",
            "tax_id",
            "bank_account",
            "total_amount",
            "line_items",
            "description",
            "quantity",
            "unit_price"
        ]
        
        # Create example format for the LLM
        example_format = """
{
  "invoice_number": "61356291",
  "invoice_date": "09/06/2012",
  "supplier_name": "Chapman, Kim and Green",
  "tax_id": "949-84-9105",
  "bank_account": "GB50ACIE59715038217063",
  "total_amount": 9,
  "line_items": [
    {
      "description": "With Hooks Stemware Storage Multiple Uses Iron Wine Rack",
      "quantity": 4,
      "unit_price": 12
    },
    {
      "description": "HOME ESSENTIALS GRADIENT STEMLESS WINE GLASSES SET OF 4",
      "quantity": 1,
      "unit_price": 28.08
    }
  ]
}
"""
        
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Your task is to extract invoice data and return it in valid JSON format."},
                {"role": "user", "content": f"""Extract the following attributes from the text: {attributes}. 
Here is the text: {text_content}
Return the data in valid JSON format as shown in this example:
{example_format}
Make sure your response is properly formatted valid JSON that can be parsed directly."""}
            ],
            stream=False
        )
        
        ai_response = response.choices[0].message.content
        
        # First, try to extract JSON from code blocks
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', ai_response)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            json_str = ai_response.strip()
        
        # Try to parse as JSON
        try:
            structured_json = json.loads(json_str)
            return {"data": structured_json, "raw_response": ai_response}
        except json.JSONDecodeError:
            # JSON parsing failed, fall back to regex extraction
            structured_json = self._extract_with_regex(json_str)
            return {"data": structured_json, "raw_response": ai_response}
    
    def _extract_with_regex(self, json_str):
        """Fallback method to extract structured data using regex when JSON parsing fails"""
        structured_json = {}
        
        # Extract invoice number
        inv_match = re.search(r'"invoice_number"\s*:\s*"([^"]+)"', json_str)
        if inv_match:
            structured_json['invoice_number'] = inv_match.group(1)
        
        # Extract invoice date
        date_match = re.search(r'"invoice_date"\s*:\s*"([^"]+)"', json_str)
        if date_match:
            structured_json['invoice_date'] = date_match.group(1)
        
        # Extract supplier name
        supplier_match = re.search(r'"supplier_name"\s*:\s*"([^"]+)"', json_str)
        if supplier_match:
            structured_json['supplier_name'] = supplier_match.group(1)
        
        # Extract tax ID
        tax_match = re.search(r'"tax_id"\s*:\s*"([^"]+)"', json_str)
        if tax_match:
            structured_json['tax_id'] = tax_match.group(1)
        
        # Extract bank account
        bank_match = re.search(r'"bank_account"\s*:\s*"([^"]+)"', json_str)
        if bank_match:
            structured_json['bank_account'] = bank_match.group(1)
        
        # Extract total amount
        total_match = re.search(r'"total_amount"\s*:\s*(\d+\.?\d*)', json_str)
        if total_match:
            structured_json['total_amount'] = float(total_match.group(1))
        
        # Extract line items
        structured_json['line_items'] = []
        
        # Find all description-quantity-price groups
        item_matches = re.finditer(r'"description"\s*:\s*"([^"]*)"\s*,\s*"quantity"\s*:\s*(\d+\.?\d*)\s*,\s*"unit_price"\s*:\s*(\d+\.?\d*)', json_str)
        
        for match in item_matches:
            item = {
                'description': match.group(1),
                'quantity': float(match.group(2)),
                'unit_price': float(match.group(3))
            }
            structured_json['line_items'].append(item)
        
        return structured_json
    
    def extract_invoice_data(self, text, contract_start=None, contract_end=None):
        """Extract structured invoice data from text"""
        try:
            lines = text.splitlines()
            invoice = {}

            def get_next_nonempty(index):
                for i in range(index + 1, len(lines)):
                    if lines[i].strip():
                        return lines[i].strip()
                return ""

            for i, line in enumerate(lines):
                line_clean = line.strip().lower()
                combined_text = line + " " + get_next_nonempty(i)

                if "invoice no" in line_clean or "invoice number" in line_clean:
                    match = re.search(r'\d+', combined_text)
                    if match:
                        invoice['invoice_number'] = match.group(0)

                elif "supplier" in line_clean or "seller" in line_clean:
                    invoice['supplier_name'] = get_next_nonempty(i)

                elif "invoice date" in combined_text.lower() or "date of issue" in combined_text.lower() or "issue date" in combined_text.lower() or "date:" in combined_text.lower():
                    date_match = None
                    date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', combined_text)
                    if not date_match:
                        for j in range(i + 1, len(lines)):
                            future_line = lines[j].strip()
                            if any(keyword in future_line.lower() for keyword in ["tax id", "iban", "client", "total", "description", "qty", "summary", "items"]):
                                continue
                            date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', future_line)
                            if date_match:
                                break
                    if date_match:
                        invoice['invoice_date'] = date_match.group(1)

                elif "service period" in line_clean:
                    date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', combined_text.strip())
                    if date_match:
                        invoice['service_date'] = date_match.group(1)

                elif "due date" in line_clean:
                    date_match = re.search(r'(\d{1,2}[./-]\d{1,2}[./-]\d{4}|\d{4}[./-]\d{1,2}[./-]\d{1,2})', combined_text.strip())
                    if date_match:
                        invoice['due_date'] = date_match.group(1)

                elif "tax id" in line_clean and 'tax_id' not in invoice:
                    match = re.search(r'[\d-]+', combined_text)
                    if match:
                        invoice['tax_id'] = match.group(0)

                elif "bank account" in line_clean or "iban" in line_clean:
                    bank_match = re.search(r'[A-Z]{2}\d{2}[A-Z0-9]{10,30}', combined_text)
                    if bank_match:
                        invoice['bank_account'] = bank_match.group(0)

                elif "total amount" in line_clean or "total" in line_clean:
                    total_match = re.search(r'\$?\s?(\d{1,3}(?:[.,]\d{2})?)', line)
                    if not total_match:
                        for j in range(i+1, min(i+4, len(lines))):
                            future_line = lines[j]
                            total_match = re.search(r'\$?\s?(\d{1,3}(?:[.,]\d{2})?)', future_line)
                            if total_match:
                                break
                    if total_match:
                        invoice['total_amount'] = float(total_match.group(1).replace(",", "."))

            invoice['line_items'] = []
            current_item = {}
            net_prices = []
            quantities = []
            collecting_prices = False

            for i, line in enumerate(lines):
                line = line.strip()
                if re.match(r'^\d+\.\s', line):
                    if current_item:
                        invoice['line_items'].append(current_item)
                    match = re.match(r'^\d+\.\s(.+?)\s(\d{1,3}[.,]\d{2})$', line)
                    if match:
                        desc = match.group(1).strip()
                        qty = float(match.group(2).replace(",", "."))
                        current_item = {
                            'description': desc,
                            'quantity': qty,
                            'unit_price': None
                        }
                    else:
                        desc = line.split('.', 1)[1].strip()
                        qty_match = re.search(r'(\d{1,3}[.,]\d{2})', desc)
                        qty = float(qty_match.group(1).replace(',', '.')) if qty_match else 1
                        desc = re.sub(r'(\d{1,3}[.,]\d{2})', '', desc).strip()
                        current_item = {
                            'description': desc,
                            'quantity': qty,
                            'unit_price': None
                        }
                elif current_item and not re.search(r'\d{1,3}[.,]\d{2}', line) and not any(kw in line.lower() for kw in ["summary", "vat", "net price", "gross", "client", "$"]):
                    current_item['description'] += " " + line.strip()
                elif "net price" in line.lower():
                    collecting_prices = True
                elif collecting_prices and re.match(r'^\d{1,3}[.,]\d{2}$', line):
                    net_prices.append(float(line.replace(',', '.')))
                elif current_item and ("summary" in line.lower() or i == len(lines) - 1):
                    invoice['line_items'].append(current_item)
                    current_item = {}

            if current_item:
                invoice['line_items'].append(current_item)

            for idx, item in enumerate(invoice['line_items']):
                if idx < len(net_prices):
                    item['unit_price'] = net_prices[idx]

            return invoice
        except Exception as e:
            return {}
            
    def create_download_link(self, content, filename):
        """Create a download link for text content"""
        b64 = base64.b64encode(content.encode()).decode()
        href = f'<a href="data:file/txt;base64,{b64}" download="{filename}">Download {filename}</a>'
        return href
#!/usr/bin/env python3
"""
Test PDF generator for integration tests
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from config.settings import AR_ACK_SIGNATURE

def create_test_ar_ack_pdf(client_name, case_id, output_path):
    """
    Create a test AR Ack PDF with specific client name and case ID.
    
    Args:
        client_name (str): Client name (e.g., "Test ARACK")
        case_id (str): Case ID (e.g., "50001234")
        output_path (str): Full path where PDF should be saved
    
    Returns:
        str: Path to created PDF file
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Create PDF
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    # Add AR Ack content
    y_position = height - 100
    
    # Case ID Number
    c.drawString(100, y_position, f"Case ID Number: {case_id}")
    y_position -= 30
    
    # Employee Name
    c.drawString(100, y_position, f"Employee Name: {client_name}")
    y_position -= 50
    
    # AR Ack signature text (use the actual signature from settings)
    signature_text = AR_ACK_SIGNATURE
    
    # Wrap text to fit on page
    lines = []
    words = signature_text.split()
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) < 80:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Draw wrapped text
    for line in lines:
        c.drawString(100, y_position, line)
        y_position -= 20
    
    c.save()
    return output_path

def create_invalid_pdf(output_path):
    """
    Create an invalid PDF (not AR Ack) for negative testing.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    y_position = height - 100
    c.drawString(100, y_position, "This is not an AR Ack document")
    c.drawString(100, y_position - 30, "It should be ignored by the system")
    
    c.save()
    return output_path

def create_malformed_ar_ack_pdf(output_path, missing_field="case_id"):
    """
    Create an AR Ack PDF missing required fields for error testing.
    
    Args:
        output_path (str): Path to save PDF
        missing_field (str): Which field to omit ("case_id" or "client_name")
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    c = canvas.Canvas(output_path, pagesize=letter)
    width, height = letter
    
    y_position = height - 100
    
    # Add AR Ack signature to make it detectable
    signature_text = AR_ACK_SIGNATURE
    lines = []
    words = signature_text.split()
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) < 80:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    
    # Draw AR Ack signature
    for line in lines:
        c.drawString(100, y_position, line)
        y_position -= 20
    
    y_position -= 50
    
    # Add fields based on what should be missing
    if missing_field != "case_id":
        c.drawString(100, y_position, "Case ID Number: 50001234")
        y_position -= 30
    
    if missing_field != "client_name":
        c.drawString(100, y_position, "Employee Name: Test Client")
        y_position -= 30
    
    c.save()
    return output_path

if __name__ == "__main__":
    # Test the generator
    test_pdf = create_test_ar_ack_pdf(
        "Test ARACK", 
        "50001234", 
        "tests/test_data/test_ar_ack.pdf"
    )
    print(f"Created test AR Ack PDF: {test_pdf}")
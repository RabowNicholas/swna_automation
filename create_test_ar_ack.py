#!/usr/bin/env python3
"""
Create a test AR Ack PDF for debugging
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_test_ar_ack_pdf():
    filename = "test_ar_ack_sample.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add AR Ack content
    y_position = height - 100
    
    # Case ID Number
    c.drawString(100, y_position, "Case ID Number: 123456789")
    y_position -= 30
    
    # Employee Name  
    c.drawString(100, y_position, "Employee Name: John Smith")
    y_position -= 50
    
    # AR Ack signature text
    signature_text = ("According to our records, you have been designated as the authorized "
                     "representative in the above case. As the authorized represatative, you have "
                     "the ability to receive correspondence, submit additional evidence, argue "
                     "factual or legal issues and exercise claimant rights pertaining to the above claim.")
    
    # Wrap text
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
    print(f"Created test AR Ack PDF: {filename}")
    print("Copy this file to your test folder to verify AR Ack detection works!")

if __name__ == "__main__":
    create_test_ar_ack_pdf()
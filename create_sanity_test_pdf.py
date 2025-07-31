#!/usr/bin/env python3
"""
Create a test AR Ack PDF for sanity testing
"""

import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

def create_sanity_test_pdf():
    """Create test AR Ack PDF for sanity testing."""
    
    # AR Ack signature text
    AR_ACK_SIGNATURE = "According to our records, you have been designated as the authorized representative in the above case. As the authorized representative, you have the ability to receive correspondence, submit additional evidence, argue factual or legal issues and exercise claimant rights pertaining to the above claim."
    
    filename = "SANITY_TEST_AR_ACK.pdf"
    
    # Create PDF
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter
    
    # Add header
    y_position = height - 100
    c.drawString(100, y_position, "*** SANITY TEST - DELETE AFTER TESTING ***")
    y_position -= 50
    
    # Case ID Number - Use a numeric test case ID that won't conflict
    c.drawString(100, y_position, "Case ID Number: 99999999")
    y_position -= 30
    
    # Employee Name - Use a test client that should exist in your Airtable  
    c.drawString(100, y_position, "Employee Name: Test Client")
    y_position -= 50
    
    # AR Ack signature text
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
    print(f"✅ Created sanity test PDF: {filename}")
    print("⚠️  REMEMBER: This contains test data - delete after testing!")
    return filename

if __name__ == "__main__":
    create_sanity_test_pdf()
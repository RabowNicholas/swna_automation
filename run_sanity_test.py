#!/usr/bin/env python3
"""
Automated Sanity Test Runner - Uses current dated temp folder
"""

import os
import sys
import shutil
from find_current_temp_folder import find_current_temp_folder
from src.processing_pipeline import ProcessingPipeline
from src.logger import SWNALogger

def run_sanity_test():
    """Run the complete sanity test automatically."""
    
    print("🧪 SWNA Automation Sanity Test")
    print("=" * 50)
    
    # Step 1: Find current temp folder
    print("📁 Finding current temp folder...")
    temp_folder = find_current_temp_folder()
    
    if not temp_folder:
        print("❌ ERROR: No Daily Temp Scans folder found!")
        print("💡 Create a folder like '1. Daily Temp Scans 8.01.25' and try again.")
        return False
    
    print(f"✅ Using temp folder: {os.path.basename(temp_folder)}")
    
    # Step 2: Check if test PDF exists
    test_pdf_name = "SANITY_TEST_AR_ACK.pdf"
    if not os.path.exists(test_pdf_name):
        print(f"❌ ERROR: {test_pdf_name} not found!")
        print("💡 Run: python create_sanity_test_pdf.py")
        return False
    
    # Step 3: Copy test PDF to temp folder
    test_pdf_path = os.path.join(temp_folder, test_pdf_name)
    print(f"📄 Copying test PDF to: {temp_folder}")
    
    try:
        shutil.copy2(test_pdf_name, test_pdf_path)
        print("✅ Test PDF copied successfully")
    except Exception as e:
        print(f"❌ ERROR: Failed to copy PDF: {e}")
        return False
    
    # Step 4: Run the pipeline test
    print("\n🚀 Running pipeline test...")
    print("-" * 50)
    
    try:
        logger = SWNALogger()
        pipeline = ProcessingPipeline(logger)
        
        result = pipeline.process_file(test_pdf_path)
        
        print("-" * 50)
        print(f"📊 Test Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
        
        # Step 5: Cleanup
        print("\n🧹 Cleaning up...")
        
        # Remove test PDF from temp folder if it's still there
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            print("✅ Removed test PDF from temp folder")
        
        # Check if file was moved successfully
        from config.settings import SYNC_FOLDER_PATH
        client_folder = os.path.join(SYNC_FOLDER_PATH, "2. Active Clients", "Client, Test", "DOL Letters")
        
        if os.path.exists(client_folder):
            for file in os.listdir(client_folder):
                if file.startswith("AR Ack - T. Client") and "TEST123456" in file:
                    moved_file = os.path.join(client_folder, file)
                    print(f"🗂️  Found moved file: {file}")
                    
                    # Ask user if they want to clean up the moved file
                    cleanup = input("🤔 Remove test file from client folder? (y/n): ").lower().strip()
                    if cleanup == 'y':
                        os.remove(moved_file)
                        print("✅ Cleaned up moved test file")
                    else:
                        print("⚠️  Test file left in client folder - remember to clean up manually!")
        
        return result
        
    except Exception as e:
        print(f"❌ ERROR: Test failed with exception: {e}")
        
        # Emergency cleanup
        if os.path.exists(test_pdf_path):
            os.remove(test_pdf_path)
            print("🧹 Emergency cleanup: removed test PDF")
            
        return False

def check_prerequisites():
    """Check if system is ready for testing."""
    
    print("🔍 Checking prerequisites...")
    
    issues = []
    
    # Check temp folder
    temp_folder = find_current_temp_folder()
    if not temp_folder:
        issues.append("No Daily Temp Scans folder found")
    else:
        print(f"✅ Temp folder: {os.path.basename(temp_folder)}")
    
    # Check test PDF
    if not os.path.exists("SANITY_TEST_AR_ACK.pdf"):
        issues.append("SANITY_TEST_AR_ACK.pdf not found - run create_sanity_test_pdf.py")
    else:
        print("✅ Test PDF found")
    
    # Check .env file
    try:
        from config.settings import SYNC_FOLDER_PATH, AIRTABLE_PAT, AIRTABLE_BASE_ID
        if not SYNC_FOLDER_PATH or not AIRTABLE_PAT or not AIRTABLE_BASE_ID:
            issues.append(".env file missing required values")
        else:
            print("✅ Environment configuration loaded")
    except Exception as e:
        issues.append(f"Configuration error: {e}")
    
    # Check if test client folder exists (optional - will create if needed)
    from config.settings import SYNC_FOLDER_PATH
    client_folder = os.path.join(SYNC_FOLDER_PATH, "2. Active Clients", "Client, Test")
    if os.path.exists(client_folder):
        print("✅ Test client folder exists")
    else:
        print("⚠️  Test client folder doesn't exist (will be created if needed)")
    
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        return False
    else:
        print("✅ All prerequisites met!")
        return True

if __name__ == "__main__":
    print("SWNA Automation Sanity Test Runner")
    print("🚨 WARNING: This makes REAL changes to Airtable and files!")
    print()
    
    if not check_prerequisites():
        print("\n❌ Prerequisites not met. Fix issues above and try again.")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    proceed = input("🤔 Ready to run REAL sanity test? (y/n): ").lower().strip()
    
    if proceed != 'y':
        print("👋 Test cancelled. Run again when ready.")
        sys.exit(0)
    
    print()
    success = run_sanity_test()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 SANITY TEST PASSED!")
        print("✅ Your Airtable and file operations are working!")
        print("✅ System is ready for production use!")
    else:
        print("💥 SANITY TEST FAILED!")
        print("❌ Check the errors above and fix before production use.")
        print("💡 Check your Airtable credentials and folder permissions.")
    
    print("=" * 50)
#!/usr/bin/env python3
"""
Quick sanity test - just check if everything connects
"""

import os
from find_current_temp_folder import find_current_temp_folder
from src.processing_pipeline import ProcessingPipeline
from src.logger import SWNALogger

def quick_test():
    """Run a quick test to verify everything works."""
    
    print("🧪 Quick Sanity Test")
    print("=" * 30)
    
    # Find temp folder
    temp_folder = find_current_temp_folder()
    print(f"✅ Temp folder: {os.path.basename(temp_folder)}")
    
    # Check if test PDF exists
    if not os.path.exists("SANITY_TEST_AR_ACK.pdf"):
        print("❌ SANITY_TEST_AR_ACK.pdf not found")
        return
    
    # Copy to temp folder
    import shutil
    test_file = os.path.join(temp_folder, "SANITY_TEST_AR_ACK.pdf")
    shutil.copy2("SANITY_TEST_AR_ACK.pdf", test_file)
    print(f"✅ Copied test file to temp folder")
    
    # Run pipeline
    print("\n🚀 Testing pipeline...")
    try:
        logger = SWNALogger()
        pipeline = ProcessingPipeline(logger)
        result = pipeline.process_file(test_file)
        
        print(f"\n📊 Result: {'✅ SUCCESS' if result else '❌ FAILED'}")
        
        # Cleanup
        if os.path.exists(test_file):
            os.remove(test_file)
            print("🧹 Cleaned up temp file")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    quick_test()
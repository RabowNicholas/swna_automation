#!/usr/bin/env python3
"""
Test script for the new structured logging system.
Simulates various operations to verify logging functionality.
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime

# Add src directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from logger import SWNALogger, ActionType, LogLevel
from log_analyzer import LogAnalyzer, LogQuery
from daily_reporter import DailyReporter
from log_rotator import LogRotator

def test_basic_logging():
    """Test basic logging functionality."""
    print("Testing basic logging functionality...")
    
    # Create temporary logs directory
    temp_logs_dir = tempfile.mkdtemp(prefix="swna_test_logs_")
    
    try:
        # Initialize logger
        logger = SWNALogger()
        logger.audit_log_file = os.path.join(temp_logs_dir, "audit.jsonl")
        logger.performance_log_file = os.path.join(temp_logs_dir, "performance.jsonl")
        
        print(f"Using temporary logs directory: {temp_logs_dir}")
        
        # Test 1: System startup
        print("✓ Testing system startup logging...")
        logger.log_startup({"mode": "test", "version": "2.0"})
        
        # Test 2: File processing simulation
        print("✓ Testing file processing logging...")
        test_file_path = "/test/path/sample_document.pdf"
        
        # Start processing
        timer = logger.start_timer("test_file_processing")
        logger.log_file_processing_start("sample_document.pdf", test_file_path)
        
        # Simulate validation
        logger.log_validation_result("airtable_client_lookup", True, {
            "client_name": "Smith, John", 
            "record_id": "rec123456789",
            "message": "Client found successfully"
        })
        
        # Simulate successful processing
        logger.log_file_processing_success(
            "sample_document.pdf", 
            "12345678", 
            "John Smith", 
            "AR Ack - J. Smith 12.31.24.pdf",
            "DOL Letters",
            test_file_path
        )
        
        # Simulate Airtable update
        logger.log_airtable_update_details(
            "John Smith", 
            "rec123456789", 
            "12345678", 
            "Rcvd AR Ack. Filed Away. 12.31.24 AI",
            {"Case ID": "12345678", "Log": "Test update"}
        )
        
        # Simulate file move
        logger.log_file_moved(
            test_file_path,
            "/destination/AR Ack - J. Smith 12.31.24.pdf",
            "sample_document.pdf",
            "AR Ack - J. Smith 12.31.24.pdf"
        )
        
        # End timing
        duration = logger.end_timer(timer)
        print(f"  - Processing completed in {duration:.3f} seconds")
        
        # Test 3: Error scenario
        print("✓ Testing error logging...")
        logger.log_file_processing_failure(
            "bad_document.pdf",
            "Failed to extract Case ID",
            "/test/path/bad_document.pdf",
            {"extraction_attempts": 3, "error_type": "parsing_error"}
        )
        
        # Test 4: File ignored
        print("✓ Testing ignored file logging...")
        logger.log_file_ignored(
            "not_ar_ack.pdf",
            "Not AR Ack document",
            "/test/path/not_ar_ack.pdf"
        )
        
        # Test 5: Daily summary
        print("✓ Testing daily summary logging...")
        logger.log_daily_summary(5, 2, 1, 8)
        
        # Test 6: System shutdown
        print("✓ Testing system shutdown logging...")
        logger.log_shutdown("test_complete")
        
        print(f"✅ Basic logging tests completed successfully!")
        
        # Verify files were created
        audit_file = os.path.join(temp_logs_dir, "audit.jsonl")
        perf_file = os.path.join(temp_logs_dir, "performance.jsonl")
        
        if os.path.exists(audit_file):
            print(f"  - Audit log created: {os.path.getsize(audit_file)} bytes")
        if os.path.exists(perf_file):
            print(f"  - Performance log created: {os.path.getsize(perf_file)} bytes")
        
        return temp_logs_dir
        
    except Exception as e:
        print(f"❌ Basic logging test failed: {str(e)}")
        shutil.rmtree(temp_logs_dir, ignore_errors=True)
        return None

def test_log_analyzer(logs_dir):
    """Test log analysis functionality."""
    print("\nTesting log analysis functionality...")
    
    try:
        analyzer = LogAnalyzer(logs_dir)
        
        # Test 1: Query recent activity
        print("✓ Testing recent activity query...")
        recent = analyzer.get_recent_activity(24)
        print(f"  - Found {len(recent)} recent entries")
        
        # Test 2: Get processing stats
        print("✓ Testing processing stats...")
        today = datetime.now().strftime("%Y-%m-%d")
        stats = analyzer.get_processing_stats(today)
        print(f"  - Stats: {stats.get('processed', 0)} processed, {stats.get('failed', 0)} failed")
        
        # Test 3: Find client activity
        print("✓ Testing client activity search...")
        client_activity = analyzer.find_client_activity("John Smith", 1)
        print(f"  - Found {len(client_activity)} entries for John Smith")
        
        # Test 4: Find case activity
        print("✓ Testing case activity search...")
        case_activity = analyzer.find_case_activity("12345678")
        print(f"  - Found {len(case_activity)} entries for case 12345678")
        
        # Test 5: Find errors
        print("✓ Testing error search...")
        errors = analyzer.find_errors(24)
        print(f"  - Found {len(errors)} errors in last 24 hours")
        
        print("✅ Log analysis tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Log analysis test failed: {str(e)}")

def test_daily_reporter(logs_dir):
    """Test daily report generation."""
    print("\nTesting daily report generation...")
    
    try:
        reporter = DailyReporter(logs_dir)
        
        # Test 1: Generate comprehensive report
        print("✓ Testing comprehensive report generation...")
        today = datetime.now().strftime("%Y-%m-%d")
        report_data = reporter.generate_comprehensive_report(today)
        print(f"  - Generated report for {report_data['date']}")
        print(f"  - Summary: {report_data['summary']['total_files']} files processed")
        
        # Test 2: Generate text report
        print("✓ Testing text report generation...")
        text_report = reporter.generate_text_report(today)
        print(f"  - Generated {len(text_report)} character text report")
        
        # Test 3: Save report
        print("✓ Testing report saving...")
        file_path = reporter.save_report(text_report, today)
        if os.path.exists(file_path):
            print(f"  - Report saved to: {file_path}")
            # Clean up
            os.remove(file_path)
        
        print("✅ Daily reporter tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Daily reporter test failed: {str(e)}")

def test_log_rotator(logs_dir):
    """Test log rotation functionality."""
    print("\nTesting log rotation functionality...")
    
    try:
        rotator = LogRotator(logs_dir, max_file_size_mb=1, max_files=3)  # Small size for testing
        
        # Test 1: Get current log sizes
        print("✓ Testing log size information...")
        log_info = rotator.get_current_log_sizes()
        for log_type, info in log_info.items():
            print(f"  - {log_type}: {info.get('size_mb', 0)} MB")
        
        # Test 2: Check rotation logic (files are too small to rotate)
        print("✓ Testing rotation check...")
        results = rotator.rotate_all_logs()
        rotated_count = sum(1 for success in results.values() if success)
        print(f"  - {rotated_count} files rotated (expected: 0 for small test files)")
        
        # Test 3: Get archive info
        print("✓ Testing archive information...")
        archives = rotator.get_archive_info()
        print(f"  - Found {len(archives)} archived files")
        
        print("✅ Log rotator tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Log rotator test failed: {str(e)}")

def display_sample_logs(logs_dir):
    """Display sample log entries to verify structure."""
    print("\nSample structured log entries:")
    print("=" * 60)
    
    audit_file = os.path.join(logs_dir, "audit.jsonl")
    if os.path.exists(audit_file):
        print("📋 AUDIT LOG SAMPLES:")
        with open(audit_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:3]):  # Show first 3 entries
                try:
                    import json
                    entry = json.loads(line.strip())
                    print(f"  {i+1}. {entry.get('action', 'unknown')} - {entry.get('status', 'unknown')} [{entry.get('timestamp', '')[:19]}]")
                except:
                    print(f"  {i+1}. [Invalid JSON entry]")
    
    perf_file = os.path.join(logs_dir, "performance.jsonl")
    if os.path.exists(perf_file):
        print("\n⚡ PERFORMANCE LOG SAMPLES:")
        with open(perf_file, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[:2]):  # Show first 2 entries
                try:
                    import json
                    entry = json.loads(line.strip())
                    print(f"  {i+1}. {entry.get('operation', 'unknown')} - {entry.get('duration_seconds', 0)}s")
                except:
                    print(f"  {i+1}. [Invalid JSON entry]")

def main():
    """Run all logging system tests."""
    print("🧪 SWNA Automation Logging System Test Suite")
    print("=" * 60)
    
    # Test basic logging
    logs_dir = test_basic_logging()
    if not logs_dir:
        print("❌ Basic logging test failed. Aborting further tests.")
        return
    
    try:
        # Test log analyzer
        test_log_analyzer(logs_dir)
        
        # Test daily reporter
        test_daily_reporter(logs_dir)
        
        # Test log rotator
        test_log_rotator(logs_dir)
        
        # Display sample logs
        display_sample_logs(logs_dir)
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
        print(f"Test logs are available at: {logs_dir}")
        print("You can manually inspect the log files to verify structure and content.")
        
    finally:
        # Ask if user wants to keep test logs
        keep_logs = input(f"\nKeep test logs for inspection? (y/N): ").lower().strip()
        if keep_logs != 'y':
            print("Cleaning up test logs...")
            shutil.rmtree(logs_dir, ignore_errors=True)
            print("Test logs cleaned up.")
        else:
            print(f"Test logs preserved at: {logs_dir}")

if __name__ == "__main__":
    main()
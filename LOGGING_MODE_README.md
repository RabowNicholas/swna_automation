# SWNA Automation - Logging Mode

## Current Status: LOGGING ONLY MODE

The system has been modified to run in **logging-only mode** for testing and verification purposes. All actual operations (Airtable updates and file moves) are commented out, but the full processing logic runs and generates detailed logs.

## What's Active in Logging Mode

✅ **PDF Text Extraction**: Fully functional  
✅ **AR Ack Document Detection**: Fully functional  
✅ **Case ID Extraction**: Fully functional  
✅ **Client Name Extraction**: Fully functional  
✅ **Data Processing Logic**: Fully functional  
✅ **Comprehensive Logging**: All actions logged with [LOGGING MODE] prefixes  

## What's Disabled in Logging Mode

❌ **Airtable API Calls**: Commented out (simulated responses)  
❌ **File Move Operations**: Commented out (logged what would happen)  
❌ **Folder Validation**: Commented out (logged what would be checked)  

## Testing the System

1. **Configure Environment**:
   ```bash
   # Edit .env file - you can use dummy values for testing
   AIRTABLE_PAT=dummy_token_for_testing
   AIRTABLE_BASE_ID=dummy_base_for_testing
   SYNC_FOLDER_PATH=/path/to/test/folder
   LOG_LEVEL=DEBUG
   ```

2. **Create Test Folder Structure**:
   ```bash
   mkdir -p "/path/to/test/folder/1. Daily Temp Scans"
   ```

3. **Run the System**:
   ```bash
   cd swna_automation
   python main.py
   ```

4. **Test with Sample PDF**:
   - Place any PDF file in the "1. Daily Temp Scans" folder
   - Watch the logs in `logs/swna_automation.log`
   - System will process the PDF and log all actions

## Expected Log Output

You should see logs like:
```
[TIMESTAMP] [INFO] Processing started: sample.pdf
[TIMESTAMP] [INFO] AR Ack document identified: sample.pdf (if AR Ack)
[TIMESTAMP] [INFO] Data extracted - Case ID: 123456, Client: John Smith
[TIMESTAMP] [INFO] [LOGGING MODE] Would search Airtable for client: Smith, John
[TIMESTAMP] [INFO] [LOGGING MODE] Simulated finding client record: rec123456789
[TIMESTAMP] [INFO] [VALIDATION] All validations passed for Smith, John
[TIMESTAMP] [INFO] [LOGGING MODE] Would update Airtable record rec123456789 with: {...}
[TIMESTAMP] [INFO] [LOGGING MODE] Would move file: /path/sample.pdf -> /path/AR Ack - J. Smith 12.30.24.pdf
[TIMESTAMP] [INFO] Processing completed successfully: sample.pdf - Case ID: 123456, Client: John Smith
```

## Switching Back to Full Mode

When ready to enable actual operations, uncomment the following sections:

**In `src/airtable_client.py`**:
- Uncomment actual Airtable API calls
- Remove simulated responses

**In `src/file_manager.py`**:
- Uncomment file validation checks
- Uncomment actual file move operations

**In `src/processing_pipeline.py`**:
- Uncomment folder validation
- Uncomment file existence checks

Then change LOG_LEVEL back to INFO in `.env`.

## Benefits of Logging Mode

- ✅ Test the complete processing logic safely
- ✅ Verify PDF extraction and data parsing work correctly  
- ✅ See exactly what the system would do without risk
- ✅ Debug any issues with document processing
- ✅ Validate the logging system works properly
- ✅ Test with real AR Ack documents safely
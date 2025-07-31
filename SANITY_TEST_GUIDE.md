# 🧪 SWNA Automation Sanity Test Guide

## ⚠️ IMPORTANT SAFETY NOTICE
**This test will make REAL changes to your Airtable and file system!**
**Follow these steps exactly to minimize risk.**

## 📋 Prerequisites Checklist

**Before starting, ensure you have:**

1. ✅ **Backup created** (already done if you followed setup)
2. ✅ **Test client in Airtable** - You need a client record with:
   - Name format: "Client, Test" (Last, First)
   - Empty or old Case ID field
   - Existing Log field
3. ✅ **Client folder exists** at:
   ```
   [SYNC_FOLDER_PATH]/2. Active Clients/Client, Test/DOL Letters/
   ```
4. ✅ **Valid .env file** with real Airtable credentials
5. ✅ **Test PDF created** (SANITY_TEST_AR_ACK.pdf)

## 🔧 Step-by-Step Test Procedure

### Phase 1: Environment Check
1. **Verify your .env file**:
   ```bash
   cat .env
   ```
   Should show:
   - AIRTABLE_PAT=your_real_token
   - AIRTABLE_BASE_ID=your_real_base_id
   - SYNC_FOLDER_PATH=your_real_path

2. **Test folder structure**:
   ```bash
   ls -la "$SYNC_FOLDER_PATH/1. Daily Temp Scans"
   ls -la "$SYNC_FOLDER_PATH/2. Active Clients/Client, Test/DOL Letters"
   ```

### Phase 2: Create Test Environment

3. **Create test client folder** (if doesn't exist):
   ```bash
   mkdir -p "$SYNC_FOLDER_PATH/2. Active Clients/Client, Test/DOL Letters"
   ```

4. **Place test PDF**:
   ```bash
   cp SANITY_TEST_AR_ACK.pdf "$SYNC_FOLDER_PATH/1. Daily Temp Scans/"
   ```

### Phase 3: Run Single File Test

5. **Start with dry run check**:
   ```bash
   python -c "
   from src.processing_pipeline import ProcessingPipeline
   from src.logger import SWNALogger
   import os
   
   logger = SWNALogger()
   pipeline = ProcessingPipeline(logger)
   
   test_file = os.path.join(os.environ['SYNC_FOLDER_PATH'], '1. Daily Temp Scans', 'SANITY_TEST_AR_ACK.pdf')
   print(f'Test file exists: {os.path.exists(test_file)}')
   print(f'Test file path: {test_file}')
   "
   ```

6. **Run the actual test**:
   ```bash
   python -c "
   from src.processing_pipeline import ProcessingPipeline
   from src.logger import SWNALogger
   import os
   
   logger = SWNALogger()
   pipeline = ProcessingPipeline(logger)
   
   test_file = os.path.join(os.environ['SYNC_FOLDER_PATH'], '1. Daily Temp Scans', 'SANITY_TEST_AR_ACK.pdf')
   
   print('🚀 Starting sanity test...')
   result = pipeline.process_file(test_file)
   print(f'✅ Test completed. Result: {result}')
   "
   ```

### Phase 4: Verify Results

7. **Check Airtable was updated**:
   - Go to your Airtable base
   - Find "Client, Test" record
   - Verify Case ID = "TEST123456"
   - Verify Log has new entry with today's date

8. **Check file was moved**:
   ```bash
   ls -la "$SYNC_FOLDER_PATH/2. Active Clients/Client, Test/DOL Letters/"
   ```
   Should show: `AR Ack - T. Client MM.DD.YY.pdf`

9. **Check original file is gone**:
   ```bash
   ls -la "$SYNC_FOLDER_PATH/1. Daily Temp Scans/SANITY_TEST_AR_ACK.pdf"
   ```
   Should show: `No such file or directory`

## ✅ Success Criteria

**Test PASSES if:**
- ✅ No errors in console output
- ✅ Airtable record updated with TEST123456 case ID
- ✅ Log entry added with today's date + " AI"
- ✅ File moved to correct client folder
- ✅ File renamed with correct format
- ✅ Original file no longer in temp folder

## ❌ Failure Scenarios & Fixes

**If test fails:**

1. **"Client not found"** → Check client name is exactly "Client, Test" in Airtable
2. **"Destination folder does not exist"** → Create the client folder manually
3. **"Airtable API error"** → Check your PAT token and base ID
4. **"Permission denied"** → Check file/folder permissions
5. **"File already exists"** → Delete the existing AR Ack file in client folder

## 🧹 Cleanup After Test

**Whether test passes or fails:**

1. **Remove test data from Airtable**:
   - Clear the Case ID field in "Client, Test" record
   - Remove the test log entry

2. **Delete test files**:
   ```bash
   rm -f "$SYNC_FOLDER_PATH/2. Active Clients/Client, Test/DOL Letters/AR Ack - T. Client"*.pdf
   rm -f SANITY_TEST_AR_ACK.pdf
   ```

3. **Optional: Restore logging mode**:
   - If you want to go back to safe logging mode
   - Restore from backup: `swna_automation_backup`

## 🚨 Emergency Rollback

**If something goes wrong:**

```bash
# Stop any running processes
# Restore from backup
rm -rf swna_automation
cp -r swna_automation_backup swna_automation
cd swna_automation

# Manual Airtable cleanup if needed
# - Remove test Case ID from client record
# - Remove test log entries
```

## 📊 Expected Output

**Successful run should look like:**
```
================================================================================
Processing started: SANITY_TEST_AR_ACK.pdf
AR Ack document identified: [path]/SANITY_TEST_AR_ACK.pdf
Data extracted - Case ID: TEST123456, Client: Test Client
[VALIDATION] Starting validation for client: Client, Test
Searching Airtable for client: Client, Test
Client record found: rec_XXXXX
[VALIDATION] Validating destination folder: [path]/DOL Letters
[VALIDATION] Generated filename: AR Ack - T. Client 07.31.25.pdf
[VALIDATION] All validations passed for Client, Test
Getting current record: rec_XXXXX
Updating Airtable record rec_XXXXX with: {'Case ID': 'TEST123456', 'Log': '...'}
Validating destination folder: [path]/DOL Letters
Moving file: [source] -> [destination]
Processing completed successfully: SANITY_TEST_AR_ACK.pdf - Case ID: TEST123456, Client: Test Client
================================================================================
```

---

## 🎯 Ready to Test?

1. ✅ Read this guide completely
2. ✅ Have your test client ready in Airtable  
3. ✅ Have your folder structure set up
4. ✅ Run the test with ONE file only
5. ✅ Verify results thoroughly
6. ✅ Clean up test data

**Time estimate: 15 minutes**

**⚠️ Remember: This makes REAL changes! Test with care!**
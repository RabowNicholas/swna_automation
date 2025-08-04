# SWNA Automation Enhanced Logging System

## Overview

The SWNA Automation system now features a comprehensive, structured logging system designed for complete action verification and easy analysis. This system provides both traditional readable logs and structured JSON logs for programmatic analysis.

## Key Features

### ✨ **Structured Audit Logging**

- **JSON format** for easy parsing and analysis
- **Complete action tracking** - every system action is logged with full context
- **Performance metrics** - timing data for all operations
- **Unique session IDs** - track related operations across the system

### 🔍 **Easy Action Verification**

- **Searchable logs** - find specific files, clients, cases, or time periods
- **Detailed context** - every log entry includes full operational context
- **Error tracking** - comprehensive error logging with stack traces and context

### 📊 **Automated Reporting**

- **Daily reports** - comprehensive summaries with recommendations
- **Performance analysis** - identify slow operations and bottlenecks
- **Error analysis** - categorize and track error patterns

### 🔄 **Log Management**

- **Automatic rotation** - prevents log files from growing too large
- **Archival system** - compressed storage of historical logs
- **Configurable retention** - control how many archived logs to keep

## File Structure

```
logs/
├── swna_automation.log      # Traditional readable logs (unchanged)
├── audit.jsonl              # Structured action audit logs (NEW)
├── performance.jsonl        # Performance timing data (NEW)
└── archive/                 # Compressed archived logs (NEW)
    ├── audit_20250731_120000.jsonl.gz
    └── performance_20250731_120000.jsonl.gz

reports/                     # Generated reports (NEW)
└── daily_report_2025-07-31.txt

src/
├── logger.py               # Enhanced logger with structured logging
├── log_analyzer.py         # Log search and analysis tools (NEW)
├── daily_reporter.py       # Automated report generation (NEW)
└── log_rotator.py          # Log rotation and archival (NEW)
```

## Usage Examples

### 🔍 **Searching Logs**

```bash
# Find all activity in last 24 hours
python3 src/log_analyzer.py --action recent --hours 24

# Get processing stats for today
python3 src/log_analyzer.py --action stats

# Find all activity for a specific client
python3 src/log_analyzer.py --action client --client "Smith, John"

# Find all activity for a specific case
python3 src/log_analyzer.py --action case --case "12345678"

# Find errors in last 6 hours
python3 src/log_analyzer.py --action errors --hours 6

# Generate daily report
python3 src/log_analyzer.py --action report --date 2025-07-31
```

### 📊 **Daily Reports**

```bash
# Generate today's report (console output)
python3 src/daily_reporter.py

# Generate and save report to file
python3 src/daily_reporter.py --save

# Generate JSON format report
python3 src/daily_reporter.py --format json

# Generate report for specific date
python3 src/daily_reporter.py --date 2025-07-30 --save
```

### 🔄 **Log Rotation**

```bash
# Check log file sizes and rotation status
python3 src/log_rotator.py --action info

# Rotate logs if they exceed size limit
python3 src/log_rotator.py --action rotate

# Force rotate all logs regardless of size
python3 src/log_rotator.py --action force

# Clean up old archived files
python3 src/log_rotator.py --action cleanup
```

## Structured Log Format

### Audit Log Entry Example

```json
{
  "timestamp": "2025-07-31T10:12:47.514",
  "session_id": "session_1722441167",
  "action_type": "file_processed",
  "level": "AUDIT",
  "pid": 12345,
  "action": "processing_success",
  "original_filename": "case-12345678.pdf",
  "new_filename": "AR Ack - J. Smith 07.31.25.pdf",
  "case_id": "12345678",
  "client_name": "John Smith",
  "destination_folder": "DOL Letters",
  "file_path": "/path/to/original/file.pdf",
  "status": "SUCCESS"
}
```

### Performance Log Entry Example

```json
{
  "timestamp": "2025-07-31T10:12:47.514",
  "session_id": "session_1722441167",
  "action_type": "file_processed",
  "level": "INFO",
  "pid": 12345,
  "operation": "file_processing_sample.pdf",
  "duration_seconds": 3.245,
  "start_time": "2025-07-31T10:12:44.269",
  "end_time": "2025-07-31T10:12:47.514"
}
```

## Action Types Tracked

- `file_processed` - Complete file processing workflow
- `file_ignored` - Files skipped (not AR Ack documents)
- `file_failed` - Processing failures with error details
- `airtable_update` - Database record updates
- `file_moved` - File relocation operations
- `validation_passed/failed` - Pre-processing validations
- `system_start/stop` - Service lifecycle events
- `daily_summary` - End-of-day statistics

## Benefits for Action Verification

### 🎯 **Complete Audit Trail**

Every action is logged with:

- **What** happened (action type and details)
- **When** it happened (precise timestamps)
- **Where** it happened (file paths, destinations)
- **Who** was involved (client names, case IDs)
- **How long** it took (performance data)
- **Why** it failed (detailed error context)

### 🔎 **Easy Investigation**

- **Find any processed file**: Search by filename, client, or case ID
- **Track processing timeline**: Follow a file through the entire workflow
- **Identify patterns**: Spot recurring errors or performance issues
- **Verify operations**: Confirm specific actions were taken

### 📈 **Performance Monitoring**

- **Processing times**: Track how long operations take
- **Bottleneck identification**: Find slow operations
- **Trend analysis**: Monitor performance over time
- **Resource optimization**: Identify areas for improvement

### 🚨 **Error Analysis**

- **Categorized errors**: Group errors by type for easier analysis
- **Error context**: Full details about what went wrong
- **Failure patterns**: Identify systematic issues
- **Quick debugging**: Rapid root cause analysis

## Daily Report Sample

```
╔══════════════════════════════════════════════════════════════╗
║               SWNA AUTOMATION DAILY REPORT                   ║
║                     July 31, 2025                          ║
╚══════════════════════════════════════════════════════════════╝

📊 PROCESSING SUMMARY:
  • Total Files Scanned: 45
  • Successfully Processed: 38
  • Files Ignored: 5
  • Processing Failures: 2
  • Success Rate: 84.4%

🔄 SYSTEM OPERATIONS:
  • Airtable Updates: 38
  • File Moves: 38
  • Unique Clients: 22
  • Unique Cases: 35

⚡ PERFORMANCE METRICS:
  • Average Processing Time: 4.2s
  • Fastest Operation: 1.1s
  • Slowest Operation: 12.8s
  • Performance Rating: GOOD
  • Fast Operations (<5s): 32
  • Slow Operations (>30s): 0

✅ ERROR ANALYSIS: 2 errors detected
  • Error Types:
    - OCR_PROCESSING: 1
    - DATA_EXTRACTION: 1

👥 CLIENT ACTIVITY:
  • Total Active Clients: 22
  • Most Active Clients:
    - Smith, John: 3 files, 3 cases
    - Johnson, Mary: 2 files, 2 cases

🏥 SYSTEM HEALTH:
  • Validation Success Rate: 94.7%
  • Health Status: GOOD
  • System Events: 2

💡 RECOMMENDATIONS:
  ✅ System operating normally - no specific recommendations
```

## Integration with Existing System

The new logging system is **fully backward compatible**:

- ✅ All existing log calls continue to work unchanged
- ✅ Traditional log file (`swna_automation.log`) still generated
- ✅ Console output remains the same
- ✅ No changes required to existing code

**New structured logs are generated automatically** alongside traditional logs, providing enhanced capabilities without disrupting current functionality.

## Testing

A comprehensive test suite is available:

```bash
python3 test_logging_system.py
```

This will:

- ✅ Test all logging functionality
- ✅ Verify structured log format
- ✅ Test search and analysis tools
- ✅ Generate sample reports
- ✅ Validate log rotation

## Configuration

The logging system uses the same configuration as before but adds new structured log files automatically. No additional setup required.

---

**Result**: You now have complete visibility into every action taken by the SWNA automation system, with powerful tools to search, analyze, and verify all operations.

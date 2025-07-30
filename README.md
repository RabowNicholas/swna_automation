# SWNA AR Acknowledgment Automation

Automated processing system for DOL AR Acknowledgment letters. Monitors folders for new PDF documents, extracts Case ID and client information, updates Airtable records, and organizes files automatically.

## Features

- **Automatic PDF Processing**: Monitors daily temp scan folders for new PDF files
- **AR Ack Detection**: Identifies AR Acknowledgment letters using signature text matching  
- **Data Extraction**: Extracts Case ID (numeric) and client names from document text
- **Airtable Integration**: Updates client records with Case ID and log entries
- **File Organization**: Renames and moves processed files to appropriate client folders
- **Atomic Operations**: All-or-nothing processing ensures data consistency
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Setup Instructions

### 1. Environment Setup

Create a Python virtual environment:
```bash
cd swna_automation
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configuration

Edit the `.env` file with your settings:

```bash
# Airtable Configuration
AIRTABLE_PAT=your_personal_access_token_here
AIRTABLE_BASE_ID=your_base_id_here

# File System Paths  
SYNC_FOLDER_PATH=/path/to/1. SWNA Shared Folder

# Processing Settings (optional)
LOG_LEVEL=INFO
```

**Required Environment Variables:**
- `AIRTABLE_PAT`: Your Airtable Personal Access Token
- `AIRTABLE_BASE_ID`: Your Airtable Base ID
- `SYNC_FOLDER_PATH`: Full path to your SWNA Shared Folder

### 3. Folder Structure Requirements

The system expects this folder structure:
```
/path/to/1. SWNA Shared Folder/
├── 1. Daily Temp Scans {MM.DD.YY}/     # Source folder (monitored)
└── 2. Active Clients/
    └── {Last, First}/
        └── DOL Letters/                  # Destination folder
```

### 4. Airtable Requirements

Your Airtable "Clients" table must have these fields:
- **Name**: Client name in format "Last, First - [XXXX]" 
- **Case ID**: Text field for storing case numbers
- **Log**: Long text field for processing history

## Running the Service

### Start the Service
```bash
python main.py
```

The service will:
1. Validate configuration
2. Process any existing PDF files in temp folders
3. Start monitoring for new files
4. Run continuously until stopped

### Stop the Service
Press `Ctrl+C` or send SIGTERM signal for graceful shutdown.

## Processing Flow

1. **Monitor**: Watches daily temp scan folders for new PDF files
2. **Identify**: Checks if document is an AR Acknowledgment letter
3. **Extract**: Gets Case ID and client name from document text
4. **Match**: Finds matching client record in Airtable
5. **Update**: Updates Airtable with Case ID and log entry
6. **Rename**: Changes filename to "AR Ack - F. Last MM.DD.YY.pdf"
7. **Move**: Places file in client's DOL Letters folder

## Document Requirements

**AR Acknowledgment letters must contain:**
- Signature text: "According to our records, you have been designated as the authorized representative..."
- Case ID Number: Numeric value following "Case ID Number:" label
- Employee Name: Client name following "Employee Name:" label

## File Naming Convention

Processed files are renamed to:
```
AR Ack - F. Last MM.DD.YY.pdf
```
Where:
- `F.` = First initial of client's first name
- `Last` = Client's last name  
- `MM.DD.YY` = Processing date

## Logging

All activities are logged to `logs/swna_automation.log`:
- **INFO**: Successful operations and status updates
- **ERROR**: Processing failures and system errors  
- **DEBUG**: Detailed processing steps (when LOG_LEVEL=DEBUG)

Log entries include timestamps and detailed information for troubleshooting.

## Error Handling

**The system fails safely:**
- If any step fails, no changes are made to Airtable or files
- Failed files remain in temp folder for manual review
- All failures are logged with detailed error messages
- System continues processing other files after failures

**Common failure scenarios:**
- Client not found in Airtable
- Destination folder doesn't exist
- Cannot extract required data from PDF
- File already exists at destination

## Troubleshooting

### Configuration Issues
- Verify all environment variables are set correctly
- Check that SYNC_FOLDER_PATH exists and is accessible
- Validate Airtable credentials and permissions

### Processing Issues  
- Check logs for detailed error messages
- Verify client folder structure exists in "2. Active Clients"
- Ensure client names in documents match Airtable exactly
- Confirm PDF files contain expected AR Ack signature text

### Performance Issues
- System processes files immediately when detected
- Large PDF files may take longer to process
- Check available disk space for file operations

## Maintenance

- Review logs daily to monitor processing activity
- Clean up old log files periodically
- Update regex patterns if document formats change
- Backup configuration and important files regularly

## Support

For issues or questions:
1. Check the logs for detailed error information
2. Verify configuration and folder structure
3. Test with a single sample document first
4. Contact system administrator if problems persist
import re
from config.settings import CASE_ID_PATTERN, CLIENT_NAME_PATTERN
from src.logger import SWNALogger
from src.document_classifier import DocumentType

class DataExtractor:
    """Extract Case ID and Client Name from various document types."""
    
    def __init__(self, logger=None):
        self.logger = logger or SWNALogger()
    
    def extract_case_id(self, text):
        """
        Extract Case ID from document text.
        Returns Case ID string or None if not found.
        """
        if not text:
            return None
        
        try:
            match = re.search(CASE_ID_PATTERN, text, re.IGNORECASE)
            if match:
                case_id = match.group(1).strip()
                # Validate that it's numeric only
                if case_id.isdigit():
                    return case_id
                else:
                    self.logger.debug(f"Case ID found but not numeric: {case_id}")
                    return None
            else:
                self.logger.debug("Case ID pattern not found in document")
                return None
                
        except Exception as e:
            self.logger.error(f"Case ID extraction failed: {str(e)}")
            return None
    
    def extract_client_name(self, text):
        """
        Extract client name from document text.
        Returns client name string or None if not found.
        """
        if not text:
            return None
        
        try:
            match = re.search(CLIENT_NAME_PATTERN, text, re.IGNORECASE)
            if match:
                full_extracted = match.group(1).strip()
                self.logger.debug(f"[NAME_EXTRACT] Full extracted text: '{full_extracted}'")
                
                # Clean up the name (remove extra spaces, normalize)
                client_name = re.sub(r'\s+', ' ', full_extracted)
                
                # Stop at the first occurrence of common company/address patterns that indicate the name has ended
                stop_patterns = [
                    r'\bTYLER\b',
                    r'\bBAILEY\b', 
                    r'\bSOUTHWEST\b',
                    r'\bNUCLEAR\b',
                    r'\bADVOCATES\b',
                    r'\b\d{2,5}\s+[A-Z]',  # Address numbers like "39 CRESCENT"
                    r'\b[A-Z]{2}\s+\d{5}\b',  # State + ZIP like "NV 89002"
                    r'\b\d{5}$',  # ZIP codes at end
                ]
                
                original_name = client_name
                for pattern in stop_patterns:
                    match_result = re.search(pattern, client_name, re.IGNORECASE)
                    if match_result:
                        # Take everything before the matched pattern
                        client_name = client_name[:match_result.start()].strip()
                        self.logger.debug(f"[NAME_EXTRACT] Stopped at pattern '{pattern}': '{original_name}' -> '{client_name}'")
                        break
                
                # Additional cleanup: remove common prefixes/suffixes that might slip through
                client_name = re.sub(r'\s+(LLC|INC|CORP|LTD)\.?$', '', client_name, flags=re.IGNORECASE).strip()
                
                self.logger.debug(f"[NAME_EXTRACT] Final cleaned name: '{client_name}'")
                
                # Basic validation - should contain at least first and last name
                name_parts = client_name.split()
                if len(name_parts) >= 2:
                    return client_name
                else:
                    self.logger.debug(f"Client name found but invalid format: {client_name}")
                    return None
            else:
                self.logger.debug("Client name pattern not found in document")
                return None
                
        except Exception as e:
            self.logger.error(f"Client name extraction failed: {str(e)}")
            return None
    
    def extract_all_data(self, text):
        """
        Extract both Case ID and Client Name from document text.
        Returns (case_id, client_name) tuple or (None, None) if extraction fails.
        """
        case_id = self.extract_case_id(text)
        client_name = self.extract_client_name(text)
        
        if case_id and client_name:
            self.logger.log_data_extracted(case_id, client_name)
            return case_id, client_name
        else:
            missing = []
            if not case_id:
                missing.append("Case ID")
            if not client_name:
                missing.append("Client Name")
            
            self.logger.debug(f"Data extraction incomplete - missing: {', '.join(missing)}")
            return None, None
    
    def format_client_name_for_matching(self, client_name):
        """
        Convert client name from 'First Last' format to 'Last, First' format for Airtable matching.
        Returns formatted name or None if formatting fails.
        """
        if not client_name:
            return None
        
        try:
            name_parts = client_name.strip().split()
            
            if len(name_parts) == 2:
                # Simple case: First Last -> Last, First
                first, last = name_parts
                return f"{last}, {first}"
            
            elif len(name_parts) > 2:
                # Complex case: First Middle Last or First Last Suffix
                # Assume last part is surname, everything else is given names
                given_names = " ".join(name_parts[:-1])
                surname = name_parts[-1]
                return f"{surname}, {given_names}"
            
            else:
                # Single name - cannot format properly
                self.logger.debug(f"Cannot format single name for matching: {client_name}")
                return None
                
        except Exception as e:
            self.logger.error(f"Client name formatting failed: {str(e)}")
            return None
    
    def extract_data_for_document_type(self, text, document_type: DocumentType):
        """
        Extract data appropriate for the given document type.
        For all document types, we need at least client name.
        For AR Ack, we also need case ID.
        
        Returns (case_id, client_name) tuple.
        """
        # Always try to extract client name for all document types
        client_name = self.extract_client_name(text)
        
        if document_type == DocumentType.AR_ACK:
            # AR Ack requires both case ID and client name
            case_id = self.extract_case_id(text)
            return case_id, client_name
        else:
            # Other document types: client name is required, case ID is optional
            case_id = self.extract_case_id(text)  # Try to get it but don't fail if missing
            return case_id, client_name
    
    def validate_extraction_for_document_type(self, case_id, client_name, document_type: DocumentType):
        """
        Validate that we have the minimum required data for the document type.
        
        Args:
            case_id: Extracted case ID (may be None)
            client_name: Extracted client name (may be None)
            document_type: The document type being processed
            
        Returns:
            True if we have minimum required data, False otherwise
        """
        if document_type == DocumentType.AR_ACK:
            # AR Ack requires both case ID and client name
            return case_id is not None and client_name is not None
        else:
            # Other document types only require client name
            return client_name is not None
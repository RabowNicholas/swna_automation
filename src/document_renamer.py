#!/usr/bin/env python3
"""
Document Renaming System for SWNA Automation
Generates appropriate filenames based on document type and extracted data.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from src.document_classifier import DocumentType, DocumentClassificationResult

class DocumentRenamer:
    """Generates filenames based on document type and extracted data."""
    
    def __init__(self, logger=None):
        self.logger = logger
    
    def generate_filename(self, classification_result: DocumentClassificationResult, 
                         client_name: str, date_override: str = None) -> str:
        """
        Generate filename based on document type, client name, and extracted data.
        
        Args:
            classification_result: Result from document classification
            client_name: Client name in "First Last" format
            date_override: Optional date override (default: current date)
        
        Returns:
            Generated filename with extension
        """
        doc_type = classification_result.document_type
        extracted_data = classification_result.extracted_data
        
        # Format client name as "F. Last"
        formatted_client = self._format_client_name(client_name)
        
        # Get date in M.D.YY format
        if date_override:
            date_str = date_override
        else:
            now = datetime.now()
            date_str = f"{now.month}.{now.day}.{str(now.year)[2:]}"
        
        # Generate base filename based on document type
        base_name = self._generate_base_name(doc_type, extracted_data)
        
        # Combine all parts
        filename = f"{base_name} - {formatted_client} {date_str}.pdf"
        
        if self.logger:
            self.logger.debug(f"Generated filename: {filename}")
        
        return filename
    
    def _format_client_name(self, client_name: str) -> str:
        """
        Format client name from "First Last" to "F. Last" format.
        
        Args:
            client_name: Full client name
            
        Returns:
            Formatted name in "F. Last" format
        """
        if not client_name or not client_name.strip():
            return "Unknown Client"
        
        parts = client_name.strip().split()
        if len(parts) >= 2:
            first_initial = parts[0][0].upper()
            last_name = parts[-1]
            return f"{first_initial}. {last_name}"
        elif len(parts) == 1:
            # If only one name, use it as last name with unknown first initial
            return f"X. {parts[0]}"
        else:
            return "Unknown Client"
    
    def _generate_base_name(self, doc_type: DocumentType, extracted_data: Dict[str, Any]) -> str:
        """
        Generate the base filename part based on document type and extracted data.
        
        Args:
            doc_type: The classified document type
            extracted_data: Data extracted during classification
            
        Returns:
            Base filename part (without client name and date)
        """
        if doc_type == DocumentType.AR_ACK:
            return "AR Ack"
        
        elif doc_type == DocumentType.CLAIM_ACK:
            return "Claim Ack"
        
        elif doc_type == DocumentType.WH_RFI:
            return "WH RFI"
        
        elif doc_type == DocumentType.IH_NOTICE:
            return "IH Notice"
        
        elif doc_type == DocumentType.RFI_POST_IH:
            return "RFI Post IH"
        
        elif doc_type == DocumentType.EN16:
            return "EN16"
        
        elif doc_type == DocumentType.RD_ACCEPT_BE:
            # Check if there's a specific amount, otherwise default to $150k
            amounts = extracted_data.get('amounts', [])
            amount = amounts[0] if amounts else "$150k"
            return f"RD Accept B&E {amount}"
        
        elif doc_type == DocumentType.RD_ACCEPT_IMPAIR:
            # Use extracted amount if available
            amounts = extracted_data.get('amounts', [])
            if amounts:
                amount = amounts[0]
                return f"RD Accept Impair {amount}"
            else:
                return "RD Accept Impair"
        
        elif doc_type == DocumentType.RD_ACCEPT_E:
            # Check for specific condition
            conditions = extracted_data.get('conditions', [])
            if conditions:
                condition = conditions[0]
                return f"RD Accept E {condition}"
            else:
                return "RD Accept E PF"  # Default to PF as shown in examples
        
        elif doc_type == DocumentType.RD_DENY:
            conditions = extracted_data.get('conditions', [])
            if conditions:
                condition = conditions[0]
                return f"RD Deny {condition}"
            else:
                return "RD Deny"
        
        elif doc_type == DocumentType.WITHDRAW_ACK:
            return "Withdraw Ack"
        
        elif doc_type == DocumentType.OBJECTION_RD_DENY_ACK:
            return "Objection to RD Deny Ack"
        
        elif doc_type == DocumentType.REMAND_ORDER:
            return "Remand Order"
        
        elif doc_type == DocumentType.FD_ACCEPT_BE:
            amounts = extracted_data.get('amounts', [])
            amount = amounts[0] if amounts else "$150k"
            return f"FD Accept B&E {amount}"
        
        elif doc_type == DocumentType.FD_ACCEPT_IMPAIR:
            amounts = extracted_data.get('amounts', [])
            if amounts:
                amount = amounts[0]
                return f"FD Accept Impair {amount}"
            else:
                return "FD Accept Impair"
        
        elif doc_type == DocumentType.FD_ACCEPT_E:
            conditions = extracted_data.get('conditions', [])
            if conditions:
                condition = conditions[0]
                return f"FD Accept E {condition}"
            else:
                return "FD Accept E"
        
        elif doc_type == DocumentType.FD_ACCEPT_CQ:
            return "FD Accept CQ"
        
        elif doc_type == DocumentType.FD_ACCEPT_CQ_SPECIFIC:
            conditions = extracted_data.get('conditions', [])
            if conditions:
                condition = conditions[0]
                return f"FD Accept CQ {condition}"
            else:
                return "FD Accept CQ"
        
        elif doc_type == DocumentType.FD_ACCEPT_IR:
            amounts = extracted_data.get('amounts', [])
            if amounts:
                amount = amounts[0]
                return f"FD Accept IR {amount}"
            else:
                return "FD Accept IR"
        
        elif doc_type == DocumentType.FD_DENY:
            conditions = extracted_data.get('conditions', [])
            if conditions:
                condition = conditions[0]
                return f"FD Deny {condition}"
            else:
                return "FD Deny"
        
        elif doc_type == DocumentType.EE11A:
            return "EE-11A"
        
        elif doc_type == DocumentType.IMPAIR_AUTH:
            return "Impair Auth"
        
        elif doc_type == DocumentType.IR_ACK:
            return "IR Ack"
        
        elif doc_type == DocumentType.IR_FOLLOW_UP:
            return "IR Follow Up"
        
        elif doc_type == DocumentType.IMPAIRMENT_FINAL_NOTICE:
            return "Impairment Final Notice"
        
        elif doc_type == DocumentType.IMPAIR_APPT_REQUEST:
            return "Impair Appt Request"
        
        elif doc_type == DocumentType.IR_DEFERRAL_NOTICE:
            return "IR Deferral Notice"
        
        elif doc_type == DocumentType.DR_IR_REPORT:
            # Format: "Dr. LastName IR ##% (##% incr)"
            doctors = extracted_data.get('doctors', [])
            percentages = extracted_data.get('percentages', [])
            is_increased = extracted_data.get('is_increased', False)
            
            if doctors and percentages:
                doctor_name = doctors[0]
                percentage = percentages[0]
                
                if is_increased and len(percentages) > 1:
                    # If there are multiple percentages and it's marked as increased
                    base_name = f"Dr. {doctor_name} IR {percentage} ({percentages[1]} incr)"
                elif is_increased:
                    base_name = f"Dr. {doctor_name} IR {percentage} (incr)"
                else:
                    base_name = f"Dr. {doctor_name} IR {percentage}"
                
                return base_name
            else:
                return "Dr IR Report"
        
        elif doc_type == DocumentType.EN20_REJECTION:
            return "EN-20 Rejection"
        
        elif doc_type == DocumentType.WL:
            return "WL"
        
        elif doc_type == DocumentType.ORAU:
            return "ORAU"
        
        elif doc_type == DocumentType.NIOSH_WAIVER:
            return "NIOSH Waiver"
        
        elif doc_type == DocumentType.DME_DENY:
            return "DME Deny"
        
        elif doc_type == DocumentType.HHC_AUTH:
            return "HHC Auth"
        
        elif doc_type == DocumentType.LMN_REQUEST:
            return "LMN Request"
        
        elif doc_type == DocumentType.ADDRESS_CHANGE_ACK:
            return "Address Change Ack"
        
        else:
            # For unknown or unhandled document types
            return "Unknown Document"
    
    def get_rename_preview(self, classification_result: DocumentClassificationResult, 
                          client_name: str, original_filename: str) -> Dict[str, Any]:
        """
        Generate a preview of the renaming operation.
        
        Args:
            classification_result: Result from document classification
            client_name: Client name
            original_filename: Current filename
            
        Returns:
            Dictionary with renaming preview information
        """
        new_filename = self.generate_filename(classification_result, client_name)
        
        return {
            'original_filename': original_filename,
            'new_filename': new_filename,
            'document_type': classification_result.document_type.value,
            'confidence': classification_result.confidence,
            'extracted_data': classification_result.extracted_data,
            'classification_reason': classification_result.classification_reason
        }
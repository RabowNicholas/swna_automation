#!/usr/bin/env python3
"""
Document Classification System for SWNA Automation
Identifies document types based on OCR text content and extracts relevant data.
"""

import re
from enum import Enum
from typing import Dict, Any, Tuple, Optional
from dataclasses import dataclass

class DocumentType(Enum):
    """Enumeration of all document types that can be processed."""
    # Keep AR_ACK first for backward compatibility
    AR_ACK = "AR Ack"
    CLAIM_ACK = "Claim Ack"
    WH_RFI = "WH RFI"
    IH_NOTICE = "IH Notice"
    RFI_POST_IH = "RFI Post IH"
    EN16 = "EN16"
    RD_ACCEPT_BE = "RD Accept B&E"
    RD_ACCEPT_IMPAIR = "RD Accept Impair"
    RD_ACCEPT_E = "RD Accept E"
    RD_DENY = "RD Deny"
    WITHDRAW_ACK = "Withdraw Ack"
    OBJECTION_RD_DENY_ACK = "Objection to RD Deny Ack"
    REMAND_ORDER = "Remand Order"
    FD_ACCEPT_BE = "FD Accept B&E"
    FD_ACCEPT_IMPAIR = "FD Accept Impair"
    FD_ACCEPT_E = "FD Accept E"
    FD_ACCEPT_CQ = "FD Accept CQ"
    FD_ACCEPT_CQ_SPECIFIC = "FD Accept CQ Specific"
    FD_ACCEPT_IR = "FD Accept IR"
    FD_DENY = "FD Deny"
    EE11A = "EE-11A"
    IMPAIR_AUTH = "Impair Auth"
    IR_ACK = "IR Ack"
    IR_FOLLOW_UP = "IR Follow Up"
    IMPAIRMENT_FINAL_NOTICE = "Impairment Final Notice"
    IMPAIR_APPT_REQUEST = "Impair Appt Request"
    IR_DEFERRAL_NOTICE = "IR Deferral Notice"
    DR_IR_REPORT = "Dr IR Report"
    EN20_REJECTION = "EN-20 Rejection"
    WL = "WL"
    ORAU = "ORAU"
    NIOSH_WAIVER = "NIOSH Waiver"
    DME_DENY = "DME Deny"
    HHC_AUTH = "HHC Auth"
    LMN_REQUEST = "LMN Request"
    ADDRESS_CHANGE_ACK = "Address Change Ack"
    UNKNOWN = "Unknown"

@dataclass
class DocumentClassificationResult:
    """Result of document classification with extracted metadata."""
    document_type: DocumentType
    confidence: float
    extracted_data: Dict[str, Any]
    classification_reason: str

class DocumentClassifier:
    """Classifies documents based on OCR text content."""
    
    def __init__(self, logger=None):
        self.logger = logger
        
        # Compile regex patterns for efficiency
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for document classification."""
        # Money patterns
        self.money_pattern = re.compile(r'\$(\d{1,3})k', re.IGNORECASE)
        self.money_range_pattern = re.compile(r'\$(\d{1,3}),?(\d{3})', re.IGNORECASE)
        
        # Percentage patterns
        self.percentage_pattern = re.compile(r'(\d{1,3})%', re.IGNORECASE)
        
        # Case ID patterns
        self.case_id_pattern = re.compile(r'case.{0,5}(\d{8})', re.IGNORECASE)
        
        # Doctor name patterns
        self.doctor_pattern = re.compile(r'Dr\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)', re.IGNORECASE)
        
        # Medical condition patterns
        self.condition_pattern = re.compile(r'\b(COPD|OSA|BCC|PF|asbestosis|mesothelioma|lung cancer)\b', re.IGNORECASE)
    
    def classify_document(self, text: str) -> DocumentClassificationResult:
        """
        Classify document based on OCR text content.
        Returns classification result with document type and extracted data.
        """
        if not text or not text.strip():
            return DocumentClassificationResult(
                DocumentType.UNKNOWN, 0.0, {}, "Empty or no text content"
            )
        
        # Clean and normalize text for better matching
        text_clean = self._clean_text(text)
        text_lower = text_clean.lower()
        
        # Try to classify document (in order of specificity)
        classification_methods = [
            self._classify_ar_ack,
            self._classify_claim_ack,
            self._classify_withdraw_ack,
            self._classify_address_change_ack,
            self._classify_objection_rd_deny_ack,
            self._classify_remand_order,
            self._classify_en16,
            self._classify_ee11a,
            self._classify_wh_rfi,
            self._classify_ih_notice,
            self._classify_rfi_post_ih,
            self._classify_rd_decisions,
            self._classify_fd_decisions,
            self._classify_impairment_docs,
            self._classify_ir_docs,
            self._classify_dr_ir_report,
            self._classify_en20_rejection,
            self._classify_wl,
            self._classify_orau,
            self._classify_niosh_waiver,
            self._classify_dme_hhc,
            self._classify_lmn_request,
        ]
        
        for method in classification_methods:
            result = method(text_clean, text_lower)
            if result and result.document_type != DocumentType.UNKNOWN:
                return result
        
        # If no classification found
        return DocumentClassificationResult(
            DocumentType.UNKNOWN, 0.0, {}, "No matching patterns found"
        )
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text for better pattern matching."""
        # Remove extra whitespace and normalize line breaks
        text = re.sub(r'\s+', ' ', text)
        # Remove common OCR artifacts
        text = re.sub(r'[^\w\s\.\-\$\%\(\)\,\:]', ' ', text)
        return text.strip()
    
    def _extract_common_data(self, text: str) -> Dict[str, Any]:
        """Extract commonly needed data from text."""
        data = {}
        
        # Extract case ID
        case_match = self.case_id_pattern.search(text)
        if case_match:
            data['case_id'] = case_match.group(1)
        
        # Extract monetary amounts
        money_matches = self.money_pattern.findall(text)
        if money_matches:
            data['amounts'] = [f"${amount}k" for amount in money_matches]
        
        # Extract percentages
        percentage_matches = self.percentage_pattern.findall(text)
        if percentage_matches:
            data['percentages'] = [f"{pct}%" for pct in percentage_matches]
        
        # Extract doctor names
        doctor_matches = self.doctor_pattern.findall(text)
        if doctor_matches:
            data['doctors'] = doctor_matches
        
        # Extract medical conditions
        condition_matches = self.condition_pattern.findall(text)
        if condition_matches:
            data['conditions'] = [cond.upper() for cond in condition_matches]
        
        return data
    
    def _classify_ar_ack(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify AR acknowledgment documents."""
        ar_indicators = [
            'acknowledgment',
            'ar ack',
            'received your claim',
            'claim has been received'
        ]
        
        if any(indicator in text_lower for indicator in ar_indicators):
            if 'asbestos' in text_lower or 'exposure' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.AR_ACK, 0.9, data, "AR acknowledgment patterns found"
                )
        
        return None
    
    def _classify_claim_ack(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify claim acknowledgment documents."""
        claim_indicators = [
            'claim acknowledgment',
            'acknowledge receipt of your claim',
            'claim has been received',
            'received your claim for benefits'
        ]
        
        if any(indicator in text_lower for indicator in claim_indicators):
            # Distinguish from AR Ack by looking for specific claim language
            if 'claim for benefits' in text_lower or 'claim acknowledgment' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.CLAIM_ACK, 0.9, data, "Claim acknowledgment patterns found"
                )
        
        return None
    
    def _classify_withdraw_ack(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify withdrawal acknowledgment documents."""
        if 'withdrawing your claim' in text_lower and 'acknowledging that withdrawal' in text_lower:
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.WITHDRAW_ACK, 0.95, data, "Withdrawal acknowledgment language found"
            )
        
        return None
    
    def _classify_address_change_ack(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify address change acknowledgment documents."""
        if 'change of address request' in text_lower and 'acknowledge receipt' in text_lower:
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.ADDRESS_CHANGE_ACK, 0.95, data, "Address change acknowledgment found"
            )
        
        return None
    
    def _classify_objection_rd_deny_ack(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify objection to RD denial acknowledgment documents."""
        objection_indicators = [
            'letter of objection',
            'object to the district office',
            'recommended decision of denial',
            'objections will be carefully considered'
        ]
        
        if any(indicator in text_lower for indicator in objection_indicators):
            if 'received within 20 days' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.OBJECTION_RD_DENY_ACK, 0.9, data, "Objection to RD denial patterns found"
                )
        
        return None
    
    def _classify_remand_order(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify remand order documents."""
        if 'remand order' in text_lower and 'file is being returned' in text_lower:
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.REMAND_ORDER, 0.95, data, "Remand order language found"
            )
        
        return None
    
    def _classify_en16(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify EN-16 form documents."""
        if 'en-16' in text_lower or 'en 16' in text_lower:
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.EN16, 0.95, data, "EN-16 form identifier found"
            )
        
        return None
    
    def _classify_ee11a(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify EE-11A form documents."""
        ee11a_indicators = [
            'ee-11a',
            'ee 11a',
            'part e',
            'whole body impairment',
            'physician must be certified'
        ]
        
        if any(indicator in text_lower for indicator in ee11a_indicators):
            if 'impairment' in text_lower and 'part e' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.EE11A, 0.9, data, "EE-11A form patterns found"
                )
        
        return None
    
    def _classify_wh_rfi(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify work history RFI documents."""
        wh_indicators = [
            'work history',
            'employment history',
            'request for information'
        ]
        
        if 'work history' in text_lower and 'request' in text_lower:
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.WH_RFI, 0.85, data, "Work history RFI patterns found"
            )
        
        return None
    
    def _classify_ih_notice(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify industrial hygienist notice documents."""
        ih_indicators = [
            'industrial hygienist',
            'industrial hygiene',
            'exposure levels',
            'toxins'
        ]
        
        if any(indicator in text_lower for indicator in ih_indicators):
            if 'work history' in text_lower and 'verified' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.IH_NOTICE, 0.85, data, "Industrial hygienist notice patterns found"
                )
        
        return None
    
    def _classify_rfi_post_ih(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify RFI post-IH documents."""
        if 'industrial hygiene' in text_lower and 'request for information' in text_lower:
            if 'dr.' in text_lower or 'doctor' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.RFI_POST_IH, 0.85, data, "RFI post-IH patterns found"
                )
        
        return None
    
    def _classify_rd_decisions(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify recommended decision documents."""
        if 'recommended decision' not in text_lower:
            return None
        
        data = self._extract_common_data(text)
        
        # Check for denial
        if 'denial' in text_lower or 'deny' in text_lower:
            return DocumentClassificationResult(
                DocumentType.RD_DENY, 0.9, data, "RD denial patterns found"
            )
        
        # Check for acceptance types
        if 'part b' in text_lower and 'part e' in text_lower and '$150' in text:
            return DocumentClassificationResult(
                DocumentType.RD_ACCEPT_BE, 0.9, data, "RD Accept B&E patterns found"
            )
        
        # Check for impairment amounts
        money_amounts = data.get('amounts', [])
        if money_amounts and 'impairment' in text_lower:
            return DocumentClassificationResult(
                DocumentType.RD_ACCEPT_IMPAIR, 0.9, data, "RD Accept Impairment patterns found"
            )
        
        # Check for Part E acceptance
        if 'part e' in text_lower and ('accept' in text_lower or 'approved' in text_lower):
            return DocumentClassificationResult(
                DocumentType.RD_ACCEPT_E, 0.85, data, "RD Accept E patterns found"
            )
        
        return None
    
    def _classify_fd_decisions(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify final decision documents."""
        if 'final decision' not in text_lower:
            return None
        
        data = self._extract_common_data(text)
        
        # Check for denial
        if 'denial' in text_lower or 'deny' in text_lower:
            return DocumentClassificationResult(
                DocumentType.FD_DENY, 0.9, data, "FD denial patterns found"
            )
        
        # Check for B&E acceptance
        if 'part b' in text_lower and 'part e' in text_lower and '$150' in text:
            return DocumentClassificationResult(
                DocumentType.FD_ACCEPT_BE, 0.9, data, "FD Accept B&E patterns found"
            )
        
        # Check for CQ acceptance (consequential condition)
        if 'consequential' in text_lower or 'cq' in text_lower:
            conditions = data.get('conditions', [])
            if conditions:
                return DocumentClassificationResult(
                    DocumentType.FD_ACCEPT_CQ_SPECIFIC, 0.9, data, "FD Accept CQ with specific condition found"
                )
            else:
                return DocumentClassificationResult(
                    DocumentType.FD_ACCEPT_CQ, 0.9, data, "FD Accept CQ patterns found"
                )
        
        # Check for IR acceptance
        money_amounts = data.get('amounts', [])
        if money_amounts and ('impairment' in text_lower or 'increased impairment' in text_lower):
            return DocumentClassificationResult(
                DocumentType.FD_ACCEPT_IR, 0.9, data, "FD Accept IR patterns found"
            )
        
        # Check for Part E acceptance
        if 'part e' in text_lower and ('accept' in text_lower or 'approved' in text_lower):
            return DocumentClassificationResult(
                DocumentType.FD_ACCEPT_E, 0.85, data, "FD Accept E patterns found"
            )
        
        return None
    
    def _classify_impairment_docs(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify impairment-related documents."""
        data = self._extract_common_data(text)
        
        # Impairment Authorization
        if 'impairment evaluation' in text_lower and 'identified you' in text_lower:
            if 'physician criteria' in text_lower or 'certified by' in text_lower:
                return DocumentClassificationResult(
                    DocumentType.IMPAIR_AUTH, 0.9, data, "Impairment authorization patterns found"
                )
        
        # IR Acknowledgment
        if 'impairment evaluation' in text_lower and 'you have selected dr' in text_lower:
            if 'no enclosed letter' in text_lower or 'form' not in text_lower:
                return DocumentClassificationResult(
                    DocumentType.IR_ACK, 0.9, data, "IR acknowledgment patterns found"
                )
        
        # IR Follow Up
        if 'received notification' in text_lower and 'impairment appt' in text_lower:
            return DocumentClassificationResult(
                DocumentType.IR_FOLLOW_UP, 0.9, data, "IR follow up patterns found"
            )
        
        # Impairment Final Notice
        if 'final notice' in text_lower and 'impairment authorization' in text_lower:
            return DocumentClassificationResult(
                DocumentType.IMPAIRMENT_FINAL_NOTICE, 0.9, data, "Impairment final notice patterns found"
            )
        
        # Impairment Appointment Request
        if 'schedule your impairment appt' in text_lower and 'within 30 days' in text_lower:
            return DocumentClassificationResult(
                DocumentType.IMPAIR_APPT_REQUEST, 0.9, data, "Impairment appointment request patterns found"
            )
        
        # IR Deferral Notice
        if 'deferral status' in text_lower and 'impairment claim' in text_lower:
            return DocumentClassificationResult(
                DocumentType.IR_DEFERRAL_NOTICE, 0.9, data, "IR deferral notice patterns found"
            )
        
        return None
    
    def _classify_ir_docs(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify IR-related documents."""
        # This would be for actual IR reports from doctors
        return None  # Will be handled by _classify_dr_ir_report
    
    def _classify_dr_ir_report(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify doctor IR report documents."""
        data = self._extract_common_data(text)
        
        # Look for doctor name + percentage + impairment context
        doctors = data.get('doctors', [])
        percentages = data.get('percentages', [])
        
        if doctors and percentages and 'impairment' in text_lower:
            # Check for increased impairment indicator
            if 'increased' in text_lower or 'incr' in text_lower:
                data['is_increased'] = True
            
            return DocumentClassificationResult(
                DocumentType.DR_IR_REPORT, 0.85, data, "Doctor IR report patterns found"
            )
        
        return None
    
    def _classify_en20_rejection(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify EN-20 rejection documents."""
        if 'en-20' in text_lower and ('rejection' in text_lower or 'errors' in text_lower):
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.EN20_REJECTION, 0.9, data, "EN-20 rejection patterns found"
            )
        
        return None
    
    def _classify_wl(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify wage loss documents."""
        if 'wage loss' in text_lower or 'wl' in text_lower:
            if 'benefits' in text_lower or 'request' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.WL, 0.85, data, "Wage loss patterns found"
                )
        
        return None
    
    def _classify_orau(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify ORAU documents."""
        if 'orau' in text_lower or 'dose reconstruction' in text_lower:
            if 'radiation' in text_lower or 'monitoring' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.ORAU, 0.9, data, "ORAU document patterns found"
                )
        
        return None
    
    def _classify_niosh_waiver(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify NIOSH waiver documents."""
        if 'niosh' in text_lower and 'waiver' in text_lower:
            data = self._extract_common_data(text)
            return DocumentClassificationResult(
                DocumentType.NIOSH_WAIVER, 0.95, data, "NIOSH waiver patterns found"
            )
        
        return None
    
    def _classify_dme_hhc(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify DME and HHC documents."""
        data = self._extract_common_data(text)
        
        if 'durable medical equipment' in text_lower or 'dme' in text_lower:
            if 'denial' in text_lower or 'deny' in text_lower:
                return DocumentClassificationResult(
                    DocumentType.DME_DENY, 0.9, data, "DME denial patterns found"
                )
        
        if 'home healthcare' in text_lower or 'hhc' in text_lower:
            if 'authorization' in text_lower or 'auth' in text_lower:
                return DocumentClassificationResult(
                    DocumentType.HHC_AUTH, 0.9, data, "HHC authorization patterns found"
                )
        
        return None
    
    def _classify_lmn_request(self, text: str, text_lower: str) -> Optional[DocumentClassificationResult]:
        """Classify Letter of Medical Necessity request documents."""
        if 'letter of medical necessity' in text_lower or 'lmn' in text_lower:
            if 'request' in text_lower:
                data = self._extract_common_data(text)
                return DocumentClassificationResult(
                    DocumentType.LMN_REQUEST, 0.9, data, "LMN request patterns found"
                )
        
        return None
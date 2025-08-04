#!/usr/bin/env python3
"""
Classification Trainer for SWNA Automation
Provides tools for manual classification correction and pattern improvement.
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import argparse
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.log_analyzer import LogAnalyzer
try:
    from src.document_classifier import DocumentClassifier, DocumentType, DocumentClassificationResult
    from src.document_processor import DocumentProcessor
    OCR_AVAILABLE = True
except ImportError as e:
    print(f"Warning: OCR dependencies not available: {e}")
    print("Some features will be limited.")
    OCR_AVAILABLE = False
    
    # Create mock classes for basic functionality
    from enum import Enum
    class DocumentType(Enum):
        UNKNOWN = "Unknown"
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
        
    class DocumentClassifier:
        def classify_document(self, text):
            return None
            
    class DocumentProcessor:
        def extract_text_from_pdf(self, file_path):
            return None


class ClassificationTrainer:
    """Tool for training and improving document classification patterns."""
    
    def __init__(self, logs_dir: str = None):
        self.analyzer = LogAnalyzer(logs_dir)
        if OCR_AVAILABLE:
            self.classifier = DocumentClassifier()
            self.processor = DocumentProcessor()
        else:
            self.classifier = None
            self.processor = None
        
        # Storage for classification corrections
        self.corrections_file = os.path.join(
            os.path.dirname(self.analyzer.logs_dir), 
            "classification_corrections.json"
        )
        self.corrections = self._load_corrections()
    
    def _load_corrections(self) -> Dict[str, Any]:
        """Load existing classification corrections."""
        if os.path.exists(self.corrections_file):
            try:
                with open(self.corrections_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load corrections file: {e}")
        
        return {
            "corrections": [],
            "pattern_suggestions": [],
            "last_updated": None
        }
    
    def _save_corrections(self):
        """Save classification corrections to file."""
        self.corrections["last_updated"] = datetime.now().isoformat()
        
        os.makedirs(os.path.dirname(self.corrections_file), exist_ok=True)
        with open(self.corrections_file, 'w') as f:
            json.dump(self.corrections, f, indent=2)
    
    def get_unknown_documents(self, date: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """Get list of documents classified as Unknown for manual review."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.analyzer.get_processing_stats(date, include_details=True)
        
        unknown_docs = []
        for file_info in stats.get("ignored_files", []):
            if file_info.get("document_type") == "Unknown":
                unknown_docs.append({
                    "filename": file_info["filename"],
                    "timestamp": file_info["timestamp"],
                    "reason": file_info.get("reason", ""),
                    "classification_reason": file_info.get("classification_reason", ""),
                    "file_path": self._find_file_path(file_info["filename"])
                })
        
        # Sort by timestamp, most recent first
        unknown_docs.sort(key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            unknown_docs = unknown_docs[:limit]
        
        return unknown_docs
    
    def _find_file_path(self, filename: str) -> Optional[str]:
        """Find the actual file path for a given filename."""
        # Check common locations
        common_paths = [
            "/Users/nicholasrabow/Sync/1. SWNA Shared Folder/1. Daily Temp Scans 8.4.25",
            "/tmp",
            "."
        ]
        
        for base_path in common_paths:
            full_path = os.path.join(base_path, filename)
            if os.path.exists(full_path):
                return full_path
        
        return None
    
    def interactive_classification_review(self, date: str = None, limit: int = 10):
        """Interactive tool for reviewing and correcting unknown classifications."""
        print("=" * 80)
        print("🔍 INTERACTIVE CLASSIFICATION REVIEW")
        print("=" * 80)
        
        unknown_docs = self.get_unknown_documents(date, limit)
        
        if not unknown_docs:
            print("✅ No unknown documents found for review!")
            return
        
        print(f"Found {len(unknown_docs)} unknown documents to review.")
        print("For each document, you can:")
        print("  • Enter the correct document type")
        print("  • Type 'skip' to skip this document")
        print("  • Type 'quit' to exit")
        print()
        
        corrections_made = 0
        
        for i, doc in enumerate(unknown_docs, 1):
            print(f"\n📄 Document {i}/{len(unknown_docs)}: {doc['filename']}")
            print(f"   Time: {doc['timestamp'][:16]}")
            print(f"   Reason: {doc['classification_reason']}")
            
            # Try to extract and show some text from the document
            if doc['file_path']:
                text_sample = self._get_document_text_sample(doc['file_path'])
                if text_sample:
                    print(f"   Sample text: {text_sample[:200]}...")
            
            # Show available document types
            print("\\nAvailable document types:")
            doc_types = [dt.value for dt in DocumentType if dt != DocumentType.UNKNOWN]
            for j, doc_type in enumerate(doc_types[:10], 1):  # Show first 10
                print(f"   {j}. {doc_type}")
            if len(doc_types) > 10:
                print(f"   ... and {len(doc_types) - 10} more")
            
            while True:
                response = input("\\nEnter document type (or number, 'skip', 'quit'): ").strip()
                
                if response.lower() == 'quit':
                    print(f"\\n✅ Review completed. Made {corrections_made} corrections.")
                    return
                elif response.lower() == 'skip':
                    break
                elif response.isdigit() and 1 <= int(response) <= len(doc_types):
                    # User entered a number
                    selected_type = doc_types[int(response) - 1]
                    self._record_correction(doc, selected_type)
                    corrections_made += 1
                    print(f"   ✅ Recorded correction: {doc['filename']} → {selected_type}")
                    break
                elif any(response.lower() == dt.value.lower() for dt in DocumentType):
                    # User entered a document type name
                    matching_type = next(dt.value for dt in DocumentType if dt.value.lower() == response.lower())
                    self._record_correction(doc, matching_type)
                    corrections_made += 1
                    print(f"   ✅ Recorded correction: {doc['filename']} → {matching_type}")
                    break
                else:
                    print("   ❌ Invalid input. Please try again.")
        
        print(f"\\n✅ Review completed. Made {corrections_made} corrections.")
        if corrections_made > 0:
            self._save_corrections()
            print(f"💾 Saved corrections to {self.corrections_file}")
    
    def _get_document_text_sample(self, file_path: str, max_chars: int = 500) -> Optional[str]:
        """Extract a sample of text from a document for review."""
        try:
            if file_path and os.path.exists(file_path) and file_path.endswith('.pdf'):
                text = self.processor.extract_text_from_pdf(file_path)
                if text:
                    # Clean up the text for display
                    text = re.sub(r'\\s+', ' ', text.strip())
                    return text[:max_chars]
        except Exception as e:
            print(f"   Warning: Could not extract text: {e}")
        
        return None
    
    def _record_correction(self, doc: Dict[str, Any], correct_type: str):
        """Record a classification correction."""
        correction = {
            "filename": doc["filename"],
            "timestamp": doc["timestamp"],
            "original_classification": "Unknown",
            "correct_classification": correct_type,
            "correction_timestamp": datetime.now().isoformat(),
            "classification_reason": doc.get("classification_reason", "")
        }
        
        self.corrections["corrections"].append(correction)
    
    def analyze_corrections(self) -> Dict[str, Any]:
        """Analyze classification corrections to identify patterns."""
        if not self.corrections["corrections"]:
            return {"message": "No corrections available for analysis"}
        
        corrections = self.corrections["corrections"]
        
        # Count corrections by type
        type_counts = {}
        for correction in corrections:
            correct_type = correction["correct_classification"]
            type_counts[correct_type] = type_counts.get(correct_type, 0) + 1
        
        # Identify frequently missed types
        frequently_missed = [(k, v) for k, v in type_counts.items() if v >= 2]
        frequently_missed.sort(key=lambda x: x[1], reverse=True)
        
        # Sample corrections for pattern analysis
        sample_corrections = corrections[-10:]  # Last 10 corrections
        
        analysis = {
            "total_corrections": len(corrections),
            "unique_types": len(type_counts),
            "type_distribution": type_counts,
            "frequently_missed": frequently_missed,
            "recent_corrections": sample_corrections,
            "analysis_timestamp": datetime.now().isoformat()
        }
        
        return analysis
    
    def suggest_pattern_improvements(self) -> List[Dict[str, Any]]:
        """Generate suggestions for improving classification patterns."""
        analysis = self.analyze_corrections()
        suggestions = []
        
        if analysis.get("frequently_missed"):
            for doc_type, count in analysis["frequently_missed"]:
                # Find sample corrections for this type
                samples = [c for c in self.corrections["corrections"] if c["correct_classification"] == doc_type]
                
                suggestion = {
                    "document_type": doc_type,
                    "frequency": count,
                    "priority": "high" if count >= 5 else "medium",
                    "description": f"{doc_type} documents are frequently misclassified ({count} corrections)",
                    "action": f"Review and improve patterns for {doc_type} detection",
                    "sample_files": [s["filename"] for s in samples[:3]]
                }
                suggestions.append(suggestion)
        
        # Add to stored suggestions
        for suggestion in suggestions:
            if suggestion not in self.corrections["pattern_suggestions"]:
                self.corrections["pattern_suggestions"].append(suggestion)
        
        return suggestions
    
    def test_classification_improvements(self, file_path: str) -> Dict[str, Any]:
        """Test classification on a specific file and show detailed results."""
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        filename = os.path.basename(file_path)
        
        try:
            # Extract text
            text = self.processor.extract_text_from_pdf(file_path)
            if not text:
                return {"error": "Could not extract text from PDF"}
            
            # Classify document
            result = self.classifier.classify_document(text)
            
            # Prepare detailed results
            test_result = {
                "filename": filename,
                "file_path": file_path,
                "classification": {
                    "document_type": result.document_type.value,
                    "confidence": result.confidence,
                    "reason": result.classification_reason,
                    "extracted_data": result.extracted_data
                },
                "text_sample": text[:500] + "..." if len(text) > 500 else text,
                "text_length": len(text),
                "test_timestamp": datetime.now().isoformat()
            }
            
            return test_result
            
        except Exception as e:
            return {"error": f"Classification test failed: {str(e)}"}
    
    def export_training_data(self, output_file: str = None) -> str:
        """Export corrections and analysis as training data."""
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"classification_training_data_{timestamp}.json"
        
        training_data = {
            "corrections": self.corrections,
            "analysis": self.analyze_corrections(),
            "suggestions": self.suggest_pattern_improvements(),
            "export_timestamp": datetime.now().isoformat(),
            "total_corrections": len(self.corrections["corrections"]),
            "document_types": list(set(c["correct_classification"] for c in self.corrections["corrections"]))
        }
        
        with open(output_file, 'w') as f:
            json.dump(training_data, f, indent=2)
        
        print(f"📊 Exported training data to {output_file}")
        return output_file


def main():
    """CLI interface for classification trainer."""
    parser = argparse.ArgumentParser(description="SWNA Classification Trainer")
    parser.add_argument("--action", choices=["review", "analyze", "suggest", "test", "export"], 
                       required=True, help="Action to perform")
    parser.add_argument("--date", help="Date for review (YYYY-MM-DD, default: today)")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of documents to review")
    parser.add_argument("--file", help="PDF file to test classification on")
    parser.add_argument("--output", help="Output file for export")
    
    args = parser.parse_args()
    
    trainer = ClassificationTrainer()
    
    if args.action == "review":
        trainer.interactive_classification_review(args.date, args.limit)
    
    elif args.action == "analyze":
        analysis = trainer.analyze_corrections()
        print("=" * 60)
        print("📊 CORRECTION ANALYSIS")
        print("=" * 60)
        
        if "message" in analysis:
            print(analysis["message"])
        else:
            print(f"Total corrections: {analysis['total_corrections']}")
            print(f"Document types corrected: {analysis['unique_types']}")
            
            if analysis.get("frequently_missed"):
                print(f"\\nFrequently missed types:")
                for doc_type, count in analysis["frequently_missed"]:
                    print(f"  • {doc_type}: {count} corrections")
    
    elif args.action == "suggest":
        suggestions = trainer.suggest_pattern_improvements()
        print("=" * 60)
        print("💡 PATTERN IMPROVEMENT SUGGESTIONS")
        print("=" * 60)
        
        if not suggestions:
            print("No suggestions available. Run corrections first.")
        else:
            for suggestion in suggestions:
                priority_icon = "🔴" if suggestion["priority"] == "high" else "🟡"
                print(f"\\n{priority_icon} {suggestion['description']}")
                print(f"   Action: {suggestion['action']}")
                if suggestion.get("sample_files"):
                    print(f"   Samples: {', '.join(suggestion['sample_files'])}")
    
    elif args.action == "test":
        if not args.file:
            print("Error: --file required for test action")
            return
        
        result = trainer.test_classification_improvements(args.file)
        print("=" * 60)
        print(f"🧪 CLASSIFICATION TEST: {os.path.basename(args.file)}")
        print("=" * 60)
        
        if "error" in result:
            print(f"❌ {result['error']}")
        else:
            classification = result["classification"]
            print(f"Document Type: {classification['document_type']}")
            print(f"Confidence: {classification['confidence']:.3f}")
            print(f"Reason: {classification['reason']}")
            
            if classification["extracted_data"]:
                print(f"Extracted Data: {classification['extracted_data']}")
            
            print(f"\\nText Sample ({result['text_length']} chars):")
            print(result["text_sample"])
    
    elif args.action == "export":
        trainer.export_training_data(args.output)


if __name__ == "__main__":
    main()
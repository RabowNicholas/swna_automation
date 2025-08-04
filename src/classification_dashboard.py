#!/usr/bin/env python3
"""
Classification Dashboard for SWNA Automation
Provides comprehensive daily monitoring and classification analytics.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from collections import defaultdict
import argparse
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from src.log_analyzer import LogAnalyzer


class ClassificationDashboard:
    """Dashboard for monitoring classification performance and daily operations."""
    
    def __init__(self, logs_dir: str = None):
        self.analyzer = LogAnalyzer(logs_dir)
    
    def generate_daily_report(self, date: str = None) -> Dict[str, Any]:
        """Generate comprehensive daily classification report."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Get detailed stats
        stats = self.analyzer.get_processing_stats(date, include_details=True)
        
        # Calculate classification metrics
        classification_metrics = self._calculate_classification_metrics(stats)
        
        # Identify improvement opportunities
        improvement_opportunities = self._identify_improvement_opportunities(stats)
        
        # Build comprehensive report
        report = {
            "date": date,
            "summary": {
                "total_files": stats["total_files"],
                "processed": stats["processed"],
                "renamed": stats.get("renamed", 0),
                "ignored": stats["ignored"],
                "failed": stats["failed"],
                "success_rate": round((stats["processed"] + stats.get("renamed", 0)) / max(stats["total_files"], 1) * 100, 1)
            },
            "classification_metrics": classification_metrics,
            "document_types": stats.get("document_types", {}),
            "improvement_opportunities": improvement_opportunities,
            "detailed_stats": stats
        }
        
        return report
    
    def _calculate_classification_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate classification accuracy and confidence metrics."""
        metrics = {
            "total_classified": 0,
            "high_confidence": 0,    # >= 0.9
            "medium_confidence": 0,  # 0.7 - 0.89
            "low_confidence": 0,     # < 0.7
            "unknown_count": 0,
            "avg_confidence": 0.0,
            "confidence_distribution": {},
            "type_accuracy": {}
        }
        
        all_confidences = []
        
        # Process renamed files (multi-document system)
        for file_info in stats.get("renamed_files", []):
            confidence = file_info.get("confidence", 0.0)
            doc_type = file_info.get("document_type", "Unknown")
            
            metrics["total_classified"] += 1
            all_confidences.append(confidence)
            
            if confidence >= 0.9:
                metrics["high_confidence"] += 1
            elif confidence >= 0.7:
                metrics["medium_confidence"] += 1
            else:
                metrics["low_confidence"] += 1
            
            # Track per-type accuracy
            if doc_type not in metrics["type_accuracy"]:
                metrics["type_accuracy"][doc_type] = {"count": 0, "avg_confidence": 0.0, "confidences": []}
            metrics["type_accuracy"][doc_type]["count"] += 1
            metrics["type_accuracy"][doc_type]["confidences"].append(confidence)
        
        # Process AR Ack files (always high confidence)
        ar_ack_count = stats.get("processed", 0)
        if ar_ack_count > 0:
            metrics["total_classified"] += ar_ack_count
            metrics["high_confidence"] += ar_ack_count
            all_confidences.extend([1.0] * ar_ack_count)
            
            metrics["type_accuracy"]["AR Ack"] = {
                "count": ar_ack_count,
                "avg_confidence": 1.0,
                "confidences": [1.0] * ar_ack_count
            }
        
        # Process ignored files
        for file_info in stats.get("ignored_files", []):
            if file_info.get("document_type") == "Unknown":
                metrics["unknown_count"] += 1
        
        # Calculate averages
        if all_confidences:
            metrics["avg_confidence"] = sum(all_confidences) / len(all_confidences)
        
        # Calculate per-type averages
        for doc_type, type_data in metrics["type_accuracy"].items():
            if type_data["confidences"]:
                type_data["avg_confidence"] = sum(type_data["confidences"]) / len(type_data["confidences"])
        
        return metrics
    
    def _identify_improvement_opportunities(self, stats: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify opportunities for classification improvement."""
        opportunities = []
        
        # Check for high volume of unknown documents
        unknown_count = len([f for f in stats.get("ignored_files", []) if f.get("document_type") == "Unknown"])
        if unknown_count > 5:
            opportunities.append({
                "type": "high_unknown_volume",
                "priority": "high",
                "count": unknown_count,
                "description": f"{unknown_count} documents classified as Unknown - potential new document types",
                "action": "Review unknown documents for new patterns"
            })
        
        # Check for low confidence classifications
        low_confidence_files = []
        for file_info in stats.get("renamed_files", []):
            if file_info.get("confidence", 0.0) < 0.7:
                low_confidence_files.append(file_info)
        
        if low_confidence_files:
            opportunities.append({
                "type": "low_confidence",
                "priority": "medium",
                "count": len(low_confidence_files),
                "description": f"{len(low_confidence_files)} documents with low confidence (<0.7)",
                "action": "Review and improve patterns for these document types",
                "files": [f["filename"] for f in low_confidence_files[:5]]  # Sample
            })
        
        # Check for extraction failures
        failed_extraction = len([f for f in stats.get("failed_files", []) if "extract required data" in f.get("reason", "")])
        if failed_extraction > 3:
            opportunities.append({
                "type": "extraction_failures",
                "priority": "medium",
                "count": failed_extraction,
                "description": f"{failed_extraction} documents failed data extraction",
                "action": "Review and improve client name/case ID extraction patterns"
            })
        
        return opportunities
    
    def print_daily_report(self, date: str = None, detailed: bool = False):
        """Print formatted daily report to console."""
        report = self.generate_daily_report(date)
        
        print("=" * 80)
        print(f"🔍 CLASSIFICATION DASHBOARD - {report['date']}")
        print("=" * 80)
        
        # Summary section
        summary = report["summary"]
        print(f"\n📊 PROCESSING SUMMARY:")
        print(f"• Total Files: {summary['total_files']}")
        print(f"• AR Ack Processed: {summary['processed']} (full processing)")
        print(f"• Other Types Renamed: {summary['renamed']} (rename only)")
        print(f"• Unknown/Ignored: {summary['ignored']}")
        print(f"• Failed: {summary['failed']}")
        print(f"• Overall Success Rate: {summary['success_rate']}%")
        
        # Document types
        if report["document_types"]:
            print(f"\n📋 DOCUMENT TYPES:")
            for doc_type, count in sorted(report["document_types"].items(), key=lambda x: x[1], reverse=True):
                print(f"  • {doc_type}: {count}")
        
        # Classification metrics
        metrics = report["classification_metrics"]
        print(f"\n🎯 CLASSIFICATION METRICS:")
        print(f"• Total Classified: {metrics['total_classified']}")
        print(f"• Average Confidence: {metrics['avg_confidence']:.2f}")
        print(f"• High Confidence (≥0.9): {metrics['high_confidence']}")
        print(f"• Medium Confidence (0.7-0.89): {metrics['medium_confidence']}")
        print(f"• Low Confidence (<0.7): {metrics['low_confidence']}")
        print(f"• Unknown Documents: {metrics['unknown_count']}")
        
        # Per-type accuracy
        if metrics["type_accuracy"] and detailed:
            print(f"\n📈 ACCURACY BY DOCUMENT TYPE:")
            for doc_type, type_data in sorted(metrics["type_accuracy"].items(), key=lambda x: x[1]["avg_confidence"], reverse=True):
                avg_conf = type_data["avg_confidence"]
                count = type_data["count"]
                print(f"  • {doc_type}: {avg_conf:.2f} avg confidence ({count} documents)")
        
        # Improvement opportunities
        opportunities = report["improvement_opportunities"]
        if opportunities:
            print(f"\n🔧 IMPROVEMENT OPPORTUNITIES:")
            for opp in opportunities:
                priority_icon = "🔴" if opp["priority"] == "high" else "🟡"
                print(f"  {priority_icon} {opp['description']}")
                print(f"     → {opp['action']}")
                if "files" in opp:
                    print(f"     → Sample files: {', '.join(opp['files'])}")
        
        print("\n" + "=" * 80)
    
    def export_unknown_documents(self, date: str = None, output_file: str = None) -> str:
        """Export unknown documents with OCR snippets for manual review."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        if output_file is None:
            output_file = f"unknown_documents_{date.replace('-', '')}.json"
        
        stats = self.analyzer.get_processing_stats(date, include_details=True)
        
        unknown_docs = []
        for file_info in stats.get("ignored_files", []):
            if file_info.get("document_type") == "Unknown":
                # Try to get OCR text snippet from logs
                ocr_snippet = self._get_ocr_snippet(file_info["filename"], date)
                
                unknown_docs.append({
                    "filename": file_info["filename"],
                    "timestamp": file_info["timestamp"],
                    "reason": file_info.get("reason", ""),
                    "classification_reason": file_info.get("classification_reason", ""),
                    "ocr_snippet": ocr_snippet
                })
        
        # Export to JSON file
        with open(output_file, 'w') as f:
            json.dump({
                "date": date,
                "unknown_documents": unknown_docs,
                "total_count": len(unknown_docs),
                "export_timestamp": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📄 Exported {len(unknown_docs)} unknown documents to {output_file}")
        return output_file
    
    def _get_ocr_snippet(self, filename: str, date: str, max_chars: int = 500) -> str:
        """Extract OCR text snippet from logs for a specific file."""
        # This would need to parse the main log file for OCR extracts
        # For now, return a placeholder
        return "OCR text snippet not available (feature in development)"
    
    def print_confidence_analysis(self, date: str = None, min_files: int = 2):
        """Print detailed confidence analysis by document type."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.analyzer.get_processing_stats(date, include_details=True)
        
        # Collect confidence data by document type
        type_confidences = defaultdict(list)
        
        for file_info in stats.get("renamed_files", []):
            doc_type = file_info.get("document_type", "Unknown")
            confidence = file_info.get("confidence", 0.0)
            type_confidences[doc_type].append(confidence)
        
        # Add AR Ack (always 1.0)
        if stats.get("processed", 0) > 0:
            type_confidences["AR Ack"] = [1.0] * stats["processed"]
        
        print("=" * 60)
        print(f"📊 CONFIDENCE ANALYSIS - {date}")
        print("=" * 60)
        
        for doc_type, confidences in sorted(type_confidences.items()):
            if len(confidences) >= min_files:
                avg_conf = sum(confidences) / len(confidences)
                min_conf = min(confidences)
                max_conf = max(confidences)
                
                print(f"\n📋 {doc_type} ({len(confidences)} documents):")
                print(f"  • Average: {avg_conf:.3f}")
                print(f"  • Range: {min_conf:.3f} - {max_conf:.3f}")
                
                # Show confidence distribution
                high = len([c for c in confidences if c >= 0.9])
                medium = len([c for c in confidences if 0.7 <= c < 0.9])
                low = len([c for c in confidences if c < 0.7])
                
                print(f"  • Distribution: {high} high, {medium} medium, {low} low")


def main():
    """CLI interface for classification dashboard."""
    parser = argparse.ArgumentParser(description="SWNA Classification Dashboard")
    parser.add_argument("--action", choices=["report", "export-unknown", "confidence"], 
                       default="report", help="Action to perform")
    parser.add_argument("--date", help="Date for analysis (YYYY-MM-DD, default: today)")
    parser.add_argument("--detailed", "-d", action="store_true", help="Show detailed analysis")
    parser.add_argument("--output", help="Output file for export actions")
    
    args = parser.parse_args()
    
    dashboard = ClassificationDashboard()
    
    if args.action == "report":
        dashboard.print_daily_report(args.date, args.detailed)
    elif args.action == "export-unknown":
        dashboard.export_unknown_documents(args.date, args.output)
    elif args.action == "confidence":
        dashboard.print_confidence_analysis(args.date)


if __name__ == "__main__":
    main()
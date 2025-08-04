#!/usr/bin/env python3
"""
Log Analysis and Query Tools for SWNA Automation
Provides utilities to search, filter, and analyze structured log files.
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass
from enum import Enum

@dataclass
class LogQuery:
    """Query parameters for log searching."""
    action_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    client_name: Optional[str] = None
    case_id: Optional[str] = None
    filename: Optional[str] = None
    status: Optional[str] = None
    session_id: Optional[str] = None
    limit: Optional[int] = None

class LogAnalyzer:
    """Utility class for analyzing structured log files."""
    
    def __init__(self, logs_dir: str = None):
        if logs_dir is None:
            # Default to logs directory relative to this file
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        
        self.logs_dir = logs_dir
        self.audit_log_file = os.path.join(logs_dir, "audit.jsonl")
        self.performance_log_file = os.path.join(logs_dir, "performance.jsonl")
    
    def _read_jsonl_file(self, file_path: str) -> List[Dict[str, Any]]:
        """Read and parse JSONL file, returning list of log entries."""
        entries = []
        if not os.path.exists(file_path):
            return entries
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entries.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            print(f"Warning: Invalid JSON line: {line[:100]}... Error: {e}")
                            continue
        except Exception as e:
            print(f"Error reading log file {file_path}: {e}")
            
        return entries
    
    def query_audit_logs(self, query: LogQuery) -> List[Dict[str, Any]]:
        """Query audit logs with filtering parameters."""
        entries = self._read_jsonl_file(self.audit_log_file)
        filtered_entries = []
        
        for entry in entries:
            # Apply filters
            if query.action_type and entry.get("action_type") != query.action_type:
                continue
                
            if query.start_date:
                entry_date = entry.get("timestamp", "")
                if entry_date < query.start_date:
                    continue
                    
            if query.end_date:
                entry_date = entry.get("timestamp", "")
                if entry_date > query.end_date:
                    continue
                    
            if query.client_name:
                if query.client_name.lower() not in entry.get("client_name", "").lower():
                    continue
                    
            if query.case_id and entry.get("case_id") != query.case_id:
                continue
                
            if query.filename:
                filename_fields = [entry.get("filename", ""), entry.get("original_filename", ""), 
                                 entry.get("new_filename", "")]
                if not any(query.filename.lower() in field.lower() for field in filename_fields):
                    continue
                    
            if query.status and entry.get("status") != query.status:
                continue
                
            if query.session_id and entry.get("session_id") != query.session_id:
                continue
            
            filtered_entries.append(entry)
        
        # Apply limit
        if query.limit:
            filtered_entries = filtered_entries[-query.limit:]
            
        return filtered_entries
    
    def get_recent_activity(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get all activity from the last N hours."""
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = LogQuery(start_date=start_time)
        return self.query_audit_logs(query)
    
    def get_processing_stats(self, date: str = None, include_details: bool = False) -> Dict[str, Any]:
        """Get processing statistics for a specific date or today."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        start_date = f"{date}T00:00:00"
        end_date = f"{date}T23:59:59"
        
        query = LogQuery(start_date=start_date, end_date=end_date)
        entries = self.query_audit_logs(query)
        
        stats = {
            "date": date,
            "total_files": 0,
            "processed": 0,
            "ignored": 0,
            "failed": 0,
            "airtable_updates": 0,
            "file_moves": 0,
            "unique_clients": set(),
            "unique_cases": set(),
            "errors": []
        }
        
        # Add detailed action lists if requested
        if include_details:
            stats["processed_files"] = []
            stats["ignored_files"] = []
            stats["failed_files"] = []
        
        for entry in entries:
            action = entry.get("action", "")
            status = entry.get("status", "")
            
            if action == "processing_started":
                stats["total_files"] += 1
            elif status == "SUCCESS" and entry.get("action_type") == "file_processed":
                stats["processed"] += 1
                if include_details:
                    stats["processed_files"].append({
                        "filename": entry.get("new_filename", entry.get("filename", "")),
                        "original_filename": entry.get("original_filename", ""),
                        "case_id": entry.get("case_id", ""),
                        "client_name": entry.get("client_name", ""),
                        "timestamp": entry.get("timestamp", ""),
                        "destination_folder": entry.get("destination_folder", "")
                    })
            elif status == "IGNORED":
                stats["ignored"] += 1
                if include_details:
                    stats["ignored_files"].append({
                        "filename": entry.get("filename", ""),
                        "reason": entry.get("ignore_reason", ""),
                        "timestamp": entry.get("timestamp", "")
                    })
            elif status == "FAILED":
                stats["failed"] += 1
                error_info = {
                    "filename": entry.get("filename", ""),
                    "reason": entry.get("failure_reason", ""),
                    "timestamp": entry.get("timestamp", "")
                }
                stats["errors"].append(error_info)
                if include_details:
                    stats["failed_files"].append(error_info)
            elif entry.get("action_type") == "airtable_update":
                stats["airtable_updates"] += 1
            elif entry.get("action_type") == "file_moved":
                stats["file_moves"] += 1
            
            # Track unique clients and cases
            if entry.get("client_name"):
                stats["unique_clients"].add(entry["client_name"])
            if entry.get("case_id"):
                stats["unique_cases"].add(entry["case_id"])
        
        # Convert sets to counts
        stats["unique_clients"] = len(stats["unique_clients"])
        stats["unique_cases"] = len(stats["unique_cases"])
        
        return stats
    
    def format_verbose_stats(self, stats: Dict[str, Any], filter_type: str = "all") -> str:
        """Format processing stats with verbose details for specific action types."""
        output = []
        
        # Header with summary
        output.append(f"Processing stats for {stats['date']}:")
        output.append(f"Total: {stats['total_files']}, Processed: {stats['processed']}, "
                     f"Ignored: {stats['ignored']}, Failed: {stats['failed']}")
        output.append("")
        
        # Show filtered results
        if filter_type in ["all", "processed"] and stats.get("processed_files"):
            if filter_type == "processed":
                output.append(f"Showing PROCESSED files only ({len(stats['processed_files'])} of {stats['total_files']} total)")
            else:
                output.append("PROCESSED FILES:")
            output.append("")
            
            for file_info in stats["processed_files"]:
                timestamp = file_info["timestamp"][:16] if file_info["timestamp"] else "Unknown"
                filename = file_info["filename"] or file_info["original_filename"]
                case_id = file_info["case_id"]
                client_name = file_info["client_name"]
                
                output.append(f"[{timestamp}] ✅ {filename} | Case: {case_id} | Client: {client_name}")
            output.append("")
        
        if filter_type in ["all", "ignored"] and stats.get("ignored_files"):
            if filter_type == "ignored":
                output.append(f"Showing IGNORED files only ({len(stats['ignored_files'])} of {stats['total_files']} total)")
            else:
                output.append("IGNORED FILES:")
            output.append("")
            
            for file_info in stats["ignored_files"]:
                timestamp = file_info["timestamp"][:16] if file_info["timestamp"] else "Unknown"
                filename = file_info["filename"]
                reason = file_info["reason"]
                
                output.append(f"[{timestamp}] ❌ {filename} | Reason: {reason}")
            output.append("")
        
        if filter_type in ["all", "failed"] and stats.get("failed_files"):
            if filter_type == "failed":
                output.append(f"Showing FAILED files only ({len(stats['failed_files'])} of {stats['total_files']} total)")
            else:
                output.append("FAILED FILES:")
            output.append("")
            
            for file_info in stats["failed_files"]:
                timestamp = file_info["timestamp"][:16] if file_info["timestamp"] else "Unknown"
                filename = file_info["filename"]
                reason = file_info["reason"]
                
                output.append(f"[{timestamp}] ⚠️  {filename} | Error: {reason}")
            output.append("")
        
        # Handle cases where no files match the filter
        if filter_type == "processed" and not stats.get("processed_files"):
            output.append("No processed files found for this date.")
        elif filter_type == "ignored" and not stats.get("ignored_files"):
            output.append("No ignored files found for this date.")
        elif filter_type == "failed" and not stats.get("failed_files"):
            output.append("No failed files found for this date.")
        
        return "\n".join(output).strip()
    
    def find_client_activity(self, client_name: str, days: int = 30) -> List[Dict[str, Any]]:
        """Find all activity for a specific client in the last N days."""
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        query = LogQuery(client_name=client_name, start_date=start_date)
        return self.query_audit_logs(query)
    
    def find_case_activity(self, case_id: str) -> List[Dict[str, Any]]:
        """Find all activity for a specific case ID."""
        query = LogQuery(case_id=case_id)
        return self.query_audit_logs(query)
    
    def find_errors(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Find all errors in the last N hours."""
        start_date = (datetime.now() - timedelta(hours=hours)).isoformat()
        query = LogQuery(status="FAILED", start_date=start_date)
        return self.query_audit_logs(query)
    
    def get_performance_data(self, operation: str = None, hours: int = 24) -> List[Dict[str, Any]]:
        """Get performance data for specific operations."""
        entries = self._read_jsonl_file(self.performance_log_file)
        
        start_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        filtered_entries = []
        
        for entry in entries:
            if entry.get("timestamp", "") < start_time:
                continue
                
            if operation and entry.get("operation") != operation:
                continue
                
            filtered_entries.append(entry)
        
        return filtered_entries
    
    def generate_daily_report(self, date: str = None) -> str:
        """Generate a comprehensive daily report."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        stats = self.get_processing_stats(date)
        
        report = f"""
=== SWNA Automation Daily Report - {date} ===

📊 PROCESSING STATISTICS:
• Total Files Scanned: {stats['total_files']}
• Successfully Processed: {stats['processed']}
• Files Ignored: {stats['ignored']}
• Processing Failures: {stats['failed']}
• Success Rate: {round(stats['processed'] / max(stats['total_files'], 1) * 100, 1)}%

🔄 SYSTEM OPERATIONS:
• Airtable Updates: {stats['airtable_updates']}
• File Moves: {stats['file_moves']}
• Unique Clients: {stats['unique_clients']}
• Unique Cases: {stats['unique_cases']}

"""
        
        if stats['errors']:
            report += "❌ ERRORS:\n"
            for error in stats['errors'][:5]:  # Show up to 5 errors
                report += f"• {error['filename']}: {error['reason']} ({error['timestamp'][:16]})\n"
            if len(stats['errors']) > 5:
                report += f"... and {len(stats['errors']) - 5} more errors\n"
        
        report += "\n" + "=" * 50
        
        return report

def main():
    """CLI interface for log analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SWNA Automation Log Analyzer")
    parser.add_argument("--action", choices=["recent", "stats", "client", "case", "errors", "report"], 
                       required=True, help="Action to perform")
    parser.add_argument("--hours", type=int, default=24, help="Hours to look back (default: 24)")
    parser.add_argument("--date", help="Date for stats/report (YYYY-MM-DD, default: today)")
    parser.add_argument("--client", help="Client name to search for")
    parser.add_argument("--case", help="Case ID to search for")
    parser.add_argument("--limit", type=int, help="Limit number of results")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed file information for stats action")
    parser.add_argument("--filter", choices=["all", "processed", "ignored", "failed"], default="all",
                       help="Filter results by action type (use with --verbose, default: all)")
    
    args = parser.parse_args()
    
    analyzer = LogAnalyzer()
    
    if args.action == "recent":
        entries = analyzer.get_recent_activity(args.hours)
        print(f"Found {len(entries)} entries in the last {args.hours} hours:")
        for entry in entries[-10:]:  # Show last 10
            print(f"[{entry.get('timestamp', '')[:16]}] {entry.get('action', '')} - {entry.get('status', '')}")
    
    elif args.action == "stats":
        if args.verbose:
            # Get detailed stats and format with verbose output
            stats = analyzer.get_processing_stats(args.date, include_details=True)
            formatted_output = analyzer.format_verbose_stats(stats, args.filter)
            print(formatted_output)
        else:
            # Simple stats output (original behavior)
            stats = analyzer.get_processing_stats(args.date)
            print(f"Processing stats for {stats['date']}:")
            print(f"Total: {stats['total_files']}, Processed: {stats['processed']}, "
                  f"Ignored: {stats['ignored']}, Failed: {stats['failed']}")
    
    elif args.action == "client":
        if not args.client:
            print("Error: --client required for client action")
            return
        entries = analyzer.find_client_activity(args.client)
        print(f"Found {len(entries)} entries for client '{args.client}':")
        for entry in entries[-5:]:  # Show last 5
            print(f"[{entry.get('timestamp', '')[:16]}] {entry.get('action', '')} - {entry.get('status', '')}")
    
    elif args.action == "case":
        if not args.case:
            print("Error: --case required for case action")
            return
        entries = analyzer.find_case_activity(args.case)
        print(f"Found {len(entries)} entries for case '{args.case}':")
        for entry in entries:
            print(f"[{entry.get('timestamp', '')[:16]}] {entry.get('action', '')} - {entry.get('status', '')}")
    
    elif args.action == "errors":
        errors = analyzer.find_errors(args.hours)
        print(f"Found {len(errors)} errors in the last {args.hours} hours:")
        for error in errors:
            print(f"[{error.get('timestamp', '')[:16]}] {error.get('filename', '')} - {error.get('failure_reason', '')}")
    
    elif args.action == "report":
        report = analyzer.generate_daily_report(args.date)
        print(report)

if __name__ == "__main__":
    main()
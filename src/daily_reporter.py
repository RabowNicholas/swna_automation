#!/usr/bin/env python3
"""
Daily Report Generator for SWNA Automation
Generates comprehensive daily reports and can email them automatically.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from src.log_analyzer import LogAnalyzer, LogQuery
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class DailyReporter:
    """Generates comprehensive daily reports from structured logs."""
    
    def __init__(self, logs_dir: str = None, email_config: Dict[str, str] = None):
        self.analyzer = LogAnalyzer(logs_dir)
        self.email_config = email_config or {}
        
        # Report templates
        self.report_dir = os.path.join(os.path.dirname(self.analyzer.logs_dir), "reports")
        os.makedirs(self.report_dir, exist_ok=True)
    
    def generate_comprehensive_report(self, date: str = None) -> Dict[str, Any]:
        """Generate a comprehensive daily report with all metrics."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Get basic processing stats
        stats = self.analyzer.get_processing_stats(date)
        
        # Get performance data
        start_date = f"{date}T00:00:00"
        end_date = f"{date}T23:59:59"
        
        query = LogQuery(start_date=start_date, end_date=end_date)
        all_entries = self.analyzer.query_audit_logs(query)
        
        # Analyze performance metrics
        performance_metrics = self._analyze_performance(all_entries, date)
        
        # Get error analysis
        error_analysis = self._analyze_errors(stats.get('errors', []))
        
        # Get client activity summary
        client_summary = self._analyze_client_activity(all_entries)
        
        # System health metrics
        system_health = self._analyze_system_health(all_entries)
        
        return {
            "date": date,
            "generated_at": datetime.now().isoformat(),
            "summary": stats,
            "performance": performance_metrics,
            "errors": error_analysis,
            "clients": client_summary,
            "system": system_health,
            "recommendations": self._generate_recommendations(stats, error_analysis, performance_metrics)
        }
    
    def _analyze_performance(self, entries: List[Dict[str, Any]], date: str) -> Dict[str, Any]:
        """Analyze performance metrics from log entries."""
        # Get performance data from separate log file
        perf_data = self.analyzer.get_performance_data(hours=24)
        
        if not perf_data:
            return {"message": "No performance data available"}
        
        # Calculate timing statistics
        durations = [entry.get('duration_seconds', 0) for entry in perf_data]
        
        if durations:
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
            
            # Categorize performance
            fast_operations = sum(1 for d in durations if d < 5)
            slow_operations = sum(1 for d in durations if d > 30)
            
            return {
                "total_operations": len(durations),
                "average_duration": round(avg_duration, 2),
                "max_duration": round(max_duration, 2),
                "min_duration": round(min_duration, 2),
                "fast_operations": fast_operations,
                "slow_operations": slow_operations,
                "performance_rating": self._calculate_performance_rating(avg_duration, slow_operations, len(durations))
            }
        
        return {"message": "No timing data available"}
    
    def _calculate_performance_rating(self, avg_duration: float, slow_ops: int, total_ops: int) -> str:
        """Calculate overall performance rating."""
        if avg_duration < 10 and slow_ops == 0:
            return "EXCELLENT"
        elif avg_duration < 20 and slow_ops / total_ops < 0.1:
            return "GOOD"
        elif avg_duration < 30 and slow_ops / total_ops < 0.2:
            return "FAIR"
        else:
            return "NEEDS_ATTENTION"
    
    def _analyze_errors(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze error patterns and frequency."""
        if not errors:
            return {"total_errors": 0, "error_types": {}, "critical_errors": []}
        
        # Categorize errors by type/reason
        error_types = {}
        critical_errors = []
        
        for error in errors:
            reason = error.get('reason', 'Unknown')
            
            # Categorize error type
            if 'OCR' in reason or 'poppler' in reason:
                error_type = 'OCR_PROCESSING'
            elif 'Airtable' in reason:
                error_type = 'AIRTABLE_API'
            elif 'extract' in reason.lower():
                error_type = 'DATA_EXTRACTION'
            elif 'folder' in reason.lower() or 'file' in reason.lower():
                error_type = 'FILE_SYSTEM'
            else:
                error_type = 'OTHER'
            
            error_types[error_type] = error_types.get(error_type, 0) + 1
            
            # Identify critical errors (repeated failures)
            if error_type in ['AIRTABLE_API', 'FILE_SYSTEM']:
                critical_errors.append(error)
        
        return {
            "total_errors": len(errors),
            "error_types": error_types,
            "critical_errors": critical_errors[:5],  # Top 5 critical errors
            "error_rate": len(errors)  # Will be calculated as percentage in report
        }
    
    def _analyze_client_activity(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze client-specific activity patterns."""
        client_stats = {}
        
        for entry in entries:
            client_name = entry.get('client_name')
            if not client_name:
                continue
            
            if client_name not in client_stats:
                client_stats[client_name] = {
                    'files_processed': 0,
                    'airtable_updates': 0,
                    'case_ids': set()
                }
            
            action = entry.get('action', '')
            status = entry.get('status', '')
            
            if action == 'processing_success' and status == 'SUCCESS':
                client_stats[client_name]['files_processed'] += 1
            elif action == 'airtable_update':
                client_stats[client_name]['airtable_updates'] += 1
            
            case_id = entry.get('case_id')
            if case_id:
                client_stats[client_name]['case_ids'].add(case_id)
        
        # Convert sets to counts and sort by activity
        for client, stats in client_stats.items():
            stats['unique_cases'] = len(stats['case_ids'])
            del stats['case_ids']  # Remove set for JSON serialization
        
        # Sort by total activity
        sorted_clients = sorted(client_stats.items(), 
                              key=lambda x: x[1]['files_processed'], reverse=True)
        
        return {
            "total_clients": len(client_stats),
            "most_active_clients": dict(sorted_clients[:10]),
            "client_summary": client_stats
        }
    
    def _analyze_system_health(self, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall system health metrics."""
        validation_success = 0
        validation_failures = 0
        system_events = 0
        
        for entry in entries:
            action_type = entry.get('action_type', '')
            status = entry.get('status', '')
            
            if action_type == 'validation_passed':
                validation_success += 1
            elif action_type == 'validation_failed':
                validation_failures += 1
            elif action_type in ['system_start', 'system_stop']:
                system_events += 1
        
        total_validations = validation_success + validation_failures
        validation_rate = (validation_success / total_validations * 100) if total_validations > 0 else 0
        
        # Determine system health status
        if validation_rate >= 95:
            health_status = "EXCELLENT"
        elif validation_rate >= 90:
            health_status = "GOOD"
        elif validation_rate >= 80:
            health_status = "FAIR"
        else:
            health_status = "POOR"
        
        return {
            "validation_success_rate": round(validation_rate, 1),
            "total_validations": total_validations,
            "system_events": system_events,
            "health_status": health_status
        }
    
    def _generate_recommendations(self, stats: Dict[str, Any], error_analysis: Dict[str, Any], 
                                performance: Dict[str, Any]) -> List[str]:
        """Generate actionable recommendations based on the data."""
        recommendations = []
        
        # Performance recommendations
        if performance.get('performance_rating') == 'NEEDS_ATTENTION':
            recommendations.append("⚡ Performance needs attention - consider investigating slow operations")
        
        if performance.get('slow_operations', 0) > 0:
            recommendations.append(f"🐌 {performance['slow_operations']} slow operations detected - review file processing logic")
        
        # Error recommendations
        error_types = error_analysis.get('error_types', {})
        
        if error_types.get('OCR_PROCESSING', 0) > 0:
            recommendations.append("📄 OCR processing errors detected - verify poppler installation")
        
        if error_types.get('AIRTABLE_API', 0) > 0:
            recommendations.append("🔗 Airtable API errors detected - check API token and network connectivity")
        
        if error_types.get('FILE_SYSTEM', 0) > 0:
            recommendations.append("📁 File system errors detected - verify folder permissions and disk space")
        
        # Success rate recommendations
        total_files = stats.get('total_files', 0)
        failed_files = stats.get('failed', 0)
        
        if total_files > 0:
            failure_rate = (failed_files / total_files) * 100
            if failure_rate > 10:
                recommendations.append(f"⚠️ High failure rate ({failure_rate:.1f}%) - investigate common failure patterns")
            elif failure_rate > 5:
                recommendations.append(f"💡 Moderate failure rate ({failure_rate:.1f}%) - monitor for trends")
        
        # General recommendations
        if not recommendations:
            recommendations.append("✅ System operating normally - no specific recommendations")
        
        return recommendations
    
    def generate_text_report(self, date: str = None) -> str:
        """Generate a formatted text report."""
        report_data = self.generate_comprehensive_report(date)
        
        date_str = datetime.strptime(report_data['date'], '%Y-%m-%d').strftime('%B %d, %Y')
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║               SWNA AUTOMATION DAILY REPORT                   ║
║                     {date_str}                      ║
╚══════════════════════════════════════════════════════════════╝

📊 PROCESSING SUMMARY:
  • Total Files Scanned: {report_data['summary']['total_files']}
  • Successfully Processed: {report_data['summary']['processed']}
  • Files Ignored: {report_data['summary']['ignored']}
  • Processing Failures: {report_data['summary']['failed']}
  • Success Rate: {round(report_data['summary']['processed'] / max(report_data['summary']['total_files'], 1) * 100, 1)}%

🔄 SYSTEM OPERATIONS:
  • Airtable Updates: {report_data['summary']['airtable_updates']}
  • File Moves: {report_data['summary']['file_moves']}
  • Unique Clients: {report_data['summary']['unique_clients']}
  • Unique Cases: {report_data['summary']['unique_cases']}

⚡ PERFORMANCE METRICS:
"""
        
        perf = report_data['performance']
        if 'total_operations' in perf:
            report += f"""  • Average Processing Time: {perf['average_duration']}s
  • Fastest Operation: {perf['min_duration']}s
  • Slowest Operation: {perf['max_duration']}s
  • Performance Rating: {perf['performance_rating']}
  • Fast Operations (<5s): {perf['fast_operations']}
  • Slow Operations (>30s): {perf['slow_operations']}
"""
        else:
            report += f"  • {perf.get('message', 'No performance data available')}\n"
        
        # Error analysis
        errors = report_data['errors']
        if errors['total_errors'] > 0:
            report += f"""
❌ ERROR ANALYSIS:
  • Total Errors: {errors['total_errors']}
  • Error Types:
"""
            for error_type, count in errors['error_types'].items():
                report += f"    - {error_type}: {count}\n"
            
            if errors['critical_errors']:
                report += "  • Recent Critical Errors:\n"
                for error in errors['critical_errors'][:3]:
                    report += f"    - {error.get('filename', 'Unknown')}: {error.get('reason', 'Unknown')}\n"
        else:
            report += "\n✅ ERROR ANALYSIS: No errors detected today!\n"
        
        # Client activity
        clients = report_data['clients']
        report += f"""
👥 CLIENT ACTIVITY:
  • Total Active Clients: {clients['total_clients']}
"""
        
        if clients['most_active_clients']:
            report += "  • Most Active Clients:\n"
            for client, stats in list(clients['most_active_clients'].items())[:5]:
                report += f"    - {client}: {stats['files_processed']} files, {stats['unique_cases']} cases\n"
        
        # System health
        health = report_data['system']
        report += f"""
🏥 SYSTEM HEALTH:
  • Validation Success Rate: {health['validation_success_rate']}%
  • Health Status: {health['health_status']}
  • System Events: {health['system_events']}

💡 RECOMMENDATIONS:
"""
        for rec in report_data['recommendations']:
            report += f"  {rec}\n"
        
        report += f"""
────────────────────────────────────────────────────────────────
Report generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
SWNA Automation System v2.0
"""
        
        return report
    
    def save_report(self, report_text: str, date: str = None) -> str:
        """Save report to file and return file path."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        filename = f"daily_report_{date}.txt"
        file_path = os.path.join(self.report_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        return file_path
    
    def email_report(self, report_text: str, recipients: List[str], date: str = None) -> bool:
        """Email the daily report to specified recipients."""
        if not self.email_config or not recipients:
            return False
        
        try:
            if date is None:
                date = datetime.now().strftime("%Y-%m-%d")
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config.get('from_email', '')
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = f"SWNA Automation Daily Report - {date}"
            
            # Add body
            msg.attach(MIMEText(report_text, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config.get('smtp_server', ''), 
                                self.email_config.get('smtp_port', 587))
            server.starttls()
            server.login(self.email_config.get('username', ''), 
                        self.email_config.get('password', ''))
            
            text = msg.as_string()
            server.sendmail(self.email_config.get('from_email', ''), recipients, text)
            server.quit()
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {str(e)}")
            return False
    
    def generate_and_save_report(self, date: str = None, email_recipients: List[str] = None) -> str:
        """Generate, save, and optionally email the daily report."""
        if date is None:
            date = datetime.now().strftime("%Y-%m-%d")
        
        # Generate report
        report_text = self.generate_text_report(date)
        
        # Save to file
        file_path = self.save_report(report_text, date)
        print(f"Report saved to: {file_path}")
        
        # Email if recipients provided
        if email_recipients:
            success = self.email_report(report_text, email_recipients, date)
            if success:
                print(f"Report emailed to: {', '.join(email_recipients)}")
            else:
                print("Failed to email report")
        
        return file_path

def main():
    """CLI interface for daily report generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SWNA Automation Daily Report Generator")
    parser.add_argument("--date", help="Date for report (YYYY-MM-DD, default: today)")
    parser.add_argument("--save", action="store_true", help="Save report to file")
    parser.add_argument("--email", nargs="+", help="Email addresses to send report to")
    parser.add_argument("--format", choices=["text", "json"], default="text", 
                       help="Output format (default: text)")
    
    args = parser.parse_args()
    
    reporter = DailyReporter()
    
    if args.format == "json":
        # Generate JSON report
        report_data = reporter.generate_comprehensive_report(args.date)
        print(json.dumps(report_data, indent=2, default=str))
    else:
        # Generate text report
        if args.save or args.email:
            file_path = reporter.generate_and_save_report(args.date, args.email)
        else:
            # Just print to console
            report_text = reporter.generate_text_report(args.date)
            print(report_text)

if __name__ == "__main__":
    main()
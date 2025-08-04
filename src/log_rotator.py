#!/usr/bin/env python3
"""
Log Rotation and Archival System for SWNA Automation
Handles automatic rotation of log files to prevent disk space issues.
"""

import os
import gzip
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

class LogRotator:
    """Handles log file rotation and archival."""
    
    def __init__(self, logs_dir: str = None, max_file_size_mb: int = 50, max_files: int = 10):
        if logs_dir is None:
            logs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
        
        self.logs_dir = logs_dir 
        self.max_file_size = max_file_size_mb * 1024 * 1024  # Convert to bytes
        self.max_files = max_files
        
        # Files to manage
        self.log_files = {
            "main": os.path.join(logs_dir, "swna_automation.log"),
            "audit": os.path.join(logs_dir, "audit.jsonl"),
            "performance": os.path.join(logs_dir, "performance.jsonl")
        }
        
        # Archive directory
        self.archive_dir = os.path.join(logs_dir, "archive")
        os.makedirs(self.archive_dir, exist_ok=True)
    
    def should_rotate_file(self, file_path: str) -> bool:
        """Check if a file should be rotated based on size."""
        if not os.path.exists(file_path):
            return False
        
        file_size = os.path.getsize(file_path)
        return file_size > self.max_file_size
    
    def rotate_file(self, file_path: str, file_type: str) -> bool:
        """Rotate a single log file."""
        if not os.path.exists(file_path):
            return False
        
        try:
            # Generate timestamp for archive
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name = os.path.basename(file_path)
            name_parts = base_name.rsplit('.', 1)
            
            if len(name_parts) == 2:
                archive_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}.gz"
            else:
                archive_name = f"{base_name}_{timestamp}.gz"
            
            archive_path = os.path.join(self.archive_dir, archive_name)
            
            # Compress and move the file
            with open(file_path, 'rb') as f_in:
                with gzip.open(archive_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Create new empty log file
            open(file_path, 'w').close()
            
            print(f"Rotated {file_path} to {archive_path}")
            return True
            
        except Exception as e:
            print(f"Failed to rotate {file_path}: {str(e)}")
            return False
    
    def cleanup_old_archives(self):
        """Remove old archived log files beyond the retention limit."""
        try:
            # Get all archive files sorted by modification time
            archive_files = []
            for filename in os.listdir(self.archive_dir):
                if filename.endswith('.gz'):
                    file_path = os.path.join(self.archive_dir, filename)
                    mtime = os.path.getmtime(file_path)
                    archive_files.append((mtime, file_path, filename))
            
            # Sort by modification time (oldest first)
            archive_files.sort()
            
            # Remove old files if we exceed max_files
            if len(archive_files) > self.max_files:
                files_to_remove = archive_files[:len(archive_files) - self.max_files]
                
                for _, file_path, filename in files_to_remove:
                    try:
                        os.remove(file_path)
                        print(f"Removed old archive: {filename}")
                    except Exception as e:
                        print(f"Failed to remove {filename}: {str(e)}")
        
        except Exception as e:
            print(f"Failed to cleanup old archives: {str(e)}")
    
    def rotate_all_logs(self) -> Dict[str, bool]:
        """Rotate all log files that need rotation."""
        results = {}
        
        for log_type, file_path in self.log_files.items():
            if self.should_rotate_file(file_path):
                results[log_type] = self.rotate_file(file_path, log_type)
                print(f"Rotated {log_type} log: {results[log_type]}")
            else:
                results[log_type] = False  # No rotation needed
        
        # Cleanup old archives
        self.cleanup_old_archives()
        
        return results
    
    def get_archive_info(self) -> List[Dict[str, Any]]:
        """Get information about archived log files."""
        archives = []
        
        if not os.path.exists(self.archive_dir):
            return archives
        
        try:
            for filename in os.listdir(self.archive_dir):
                if filename.endswith('.gz'):
                    file_path = os.path.join(self.archive_dir, filename)
                    stat = os.stat(file_path)
                    
                    archives.append({
                        "filename": filename,
                        "path": file_path,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
            
            # Sort by creation time (newest first)
            archives.sort(key=lambda x: x["created"], reverse=True)
            
        except Exception as e:
            print(f"Failed to get archive info: {str(e)}")
        
        return archives
    
    def get_current_log_sizes(self) -> Dict[str, Dict[str, Any]]:
        """Get current log file sizes and status."""
        log_info = {}
        
        for log_type, file_path in self.log_files.items():
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                log_info[log_type] = {
                    "path": file_path,
                    "size_mb": round(size / (1024 * 1024), 2),
                    "size_bytes": size,
                    "needs_rotation": size > self.max_file_size,
                    "max_size_mb": round(self.max_file_size / (1024 * 1024), 2)
                }
            else:
                log_info[log_type] = {
                    "path": file_path,
                    "size_mb": 0,
                    "size_bytes": 0,
                    "needs_rotation": False,
                    "exists": False
                }
        
        return log_info
    
    def force_rotate_all(self) -> Dict[str, bool]:
        """Force rotation of all log files regardless of size."""
        results = {}
        
        for log_type, file_path in self.log_files.items():
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                results[log_type] = self.rotate_file(file_path, log_type)
            else:
                results[log_type] = False  # File doesn't exist or is empty
        
        self.cleanup_old_archives()
        return results

def main():
    """CLI interface for log rotation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="SWNA Automation Log Rotator")
    parser.add_argument("--action", choices=["rotate", "info", "force", "cleanup"], 
                       required=True, help="Action to perform")
    parser.add_argument("--max-size", type=int, default=50, 
                       help="Maximum file size in MB before rotation (default: 50)")
    parser.add_argument("--max-files", type=int, default=10,
                       help="Maximum number of archived files to keep (default: 10)")
    
    args = parser.parse_args()
    
    rotator = LogRotator(max_file_size_mb=args.max_size, max_files=args.max_files)
    
    if args.action == "rotate":
        print("Checking log files for rotation...")
        results = rotator.rotate_all_logs()
        
        rotated_count = sum(1 for success in results.values() if success)
        print(f"\nRotated {rotated_count} log files:")
        for log_type, success in results.items():
            status = "✓ Rotated" if success else "- No rotation needed"
            print(f"  {log_type}: {status}")
    
    elif args.action == "info":
        print("Current log file status:")
        log_info = rotator.get_current_log_sizes()
        
        for log_type, info in log_info.items():
            status = "⚠️ NEEDS ROTATION" if info.get('needs_rotation', False) else "✓ OK"
            print(f"  {log_type}: {info['size_mb']} MB {status}")
        
        print(f"\nArchived files:")
        archives = rotator.get_archive_info()
        if archives:
            for archive in archives[:5]:  # Show latest 5
                print(f"  {archive['filename']}: {archive['size_mb']} MB ({archive['created'][:10]})")
            if len(archives) > 5:
                print(f"  ... and {len(archives) - 5} more archived files")
        else:
            print("  No archived files")
    
    elif args.action == "force":
        print("Force rotating all log files...")
        results = rotator.force_rotate_all()
        
        rotated_count = sum(1 for success in results.values() if success)
        print(f"\nForce rotated {rotated_count} log files:")
        for log_type, success in results.items():
            status = "✓ Rotated" if success else "- Skipped (empty/missing)"
            print(f"  {log_type}: {status}")
    
    elif args.action == "cleanup":
        print("Cleaning up old archived files...")
        rotator.cleanup_old_archives()
        print("Cleanup completed")

if __name__ == "__main__":
    main()
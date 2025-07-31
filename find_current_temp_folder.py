#!/usr/bin/env python3
"""
Utility to find the current Daily Temp Scans folder (handles dated folders)
"""

import os
import sys
from config.settings import SYNC_FOLDER_PATH

def find_current_temp_folder():
    """
    Find the current Daily Temp Scans folder, handling dated versions.
    Returns the full path to the current temp folder or None if not found.
    """
    try:
        # Check for exact match first
        exact_match = os.path.join(SYNC_FOLDER_PATH, "1. Daily Temp Scans")
        if os.path.exists(exact_match) and os.path.isdir(exact_match):
            return exact_match
        
        # Look for dated versions
        if os.path.exists(SYNC_FOLDER_PATH):
            temp_folders = []
            for item in os.listdir(SYNC_FOLDER_PATH):
                if item.startswith("1. Daily Temp Scans"):
                    full_path = os.path.join(SYNC_FOLDER_PATH, item)
                    if os.path.isdir(full_path):
                        temp_folders.append((item, full_path))
            
            if temp_folders:
                # Sort by name (most recent date should be last alphabetically)
                temp_folders.sort(key=lambda x: x[0])
                return temp_folders[-1][1]  # Return the most recent one
        
        return None
        
    except Exception as e:
        print(f"Error finding temp folder: {e}")
        return None

def list_all_temp_folders():
    """List all Daily Temp Scans folders found."""
    try:
        temp_folders = []
        
        # Check exact match
        exact_match = os.path.join(SYNC_FOLDER_PATH, "1. Daily Temp Scans")
        if os.path.exists(exact_match) and os.path.isdir(exact_match):
            temp_folders.append(("1. Daily Temp Scans", exact_match))
        
        # Check dated versions
        if os.path.exists(SYNC_FOLDER_PATH):
            for item in os.listdir(SYNC_FOLDER_PATH):
                if item.startswith("1. Daily Temp Scans") and item != "1. Daily Temp Scans":
                    full_path = os.path.join(SYNC_FOLDER_PATH, item)
                    if os.path.isdir(full_path):
                        temp_folders.append((item, full_path))
        
        return temp_folders
        
    except Exception as e:
        print(f"Error listing temp folders: {e}")
        return []

if __name__ == "__main__":
    print("SWNA Temp Folder Finder")
    print("=" * 50)
    print(f"Sync folder path: {SYNC_FOLDER_PATH}")
    print()
    
    # List all temp folders
    all_folders = list_all_temp_folders()
    if all_folders:
        print("Found Daily Temp Scans folders:")
        for name, path in all_folders:
            print(f"  📁 {name}")
            print(f"     {path}")
        print()
    else:
        print("❌ No Daily Temp Scans folders found!")
        print()
    
    # Find current one
    current = find_current_temp_folder()
    if current:
        print(f"✅ Current temp folder: {os.path.basename(current)}")
        print(f"   Full path: {current}")
        
        # Test if we can write to it
        try:
            test_file = os.path.join(current, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print("   ✅ Write permissions: OK")
        except Exception as e:
            print(f"   ❌ Write permissions: FAILED ({e})")
            
    else:
        print("❌ No current temp folder found!")
        print("\n💡 Suggestion: Create a folder like '1. Daily Temp Scans 8.01.25'")
    
    print("\n" + "=" * 50)
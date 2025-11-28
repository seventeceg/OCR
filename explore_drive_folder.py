#!/usr/bin/env python3
"""
Explore Google Drive folder structure
Lists all files and subfolders to understand the folder organization
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import config
from src.google_drive_handler import GoogleDriveHandler

def list_all_items(handler, folder_id, indent=0):
    """List all items in folder (files and subfolders)"""
    
    query = f"'{folder_id}' in parents and trashed=false"
    
    try:
        results = handler.service.files().list(
            q=query,
            pageSize=100,
            fields="files(id, name, mimeType, size)"
        ).execute()
        
        items = results.get('files', [])
        
        if not items:
            print(f"{'  ' * indent}  (empty folder)")
            return
        
        # Separate folders and files
        folders = [item for item in items if item['mimeType'] == 'application/vnd.google-apps.folder']
        files = [item for item in items if item['mimeType'] != 'application/vnd.google-apps.folder']
        
        # List folders
        for folder in folders:
            print(f"{'  ' * indent}📁 {folder['name']} (folder)")
            list_all_items(handler, folder['id'], indent + 1)
        
        # List files
        for file in files:
            size_mb = int(file.get('size', 0)) / (1024 * 1024) if file.get('size') else 0
            mime_type = file['mimeType'].split('/')[-1]
            print(f"{'  ' * indent}📄 {file['name']} ({mime_type}, {size_mb:.2f} MB)")
            
    except Exception as e:
        print(f"{'  ' * indent}Error: {e}")

def main():
    print("=" * 70)
    print("Google Drive Folder Explorer")
    print("=" * 70)
    print(f"\nFolder ID: {config.GOOGLE_DRIVE_FOLDER_ID}")
    print("\nFolder contents:\n")
    
    try:
        handler = GoogleDriveHandler()
        list_all_items(handler, config.GOOGLE_DRIVE_FOLDER_ID)
        
        print("\n" + "=" * 70)
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

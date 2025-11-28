#!/usr/bin/env python3
"""
Setup and test Google Drive API integration
This script will authenticate and verify connection to Google Drive
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

import config
from src.google_drive_handler import GoogleDriveHandler, test_connection
from loguru import logger

def main():
    """Main setup function"""
    print("=" * 70)
    print("Google Drive API Setup and Test")
    print("=" * 70)
    
    # Check if credentials file exists
    print("\n1. Checking credentials file...")
    if not os.path.exists(config.GOOGLE_CREDENTIALS_PATH):
        print(f"❌ Credentials file not found: {config.GOOGLE_CREDENTIALS_PATH}")
        print("\nPlease ensure client.json exists in the project directory.")
        return False
    else:
        print(f"✓ Credentials file found: {config.GOOGLE_CREDENTIALS_PATH}")
    
    # Check folder ID
    print("\n2. Checking Google Drive folder ID...")
    if not config.GOOGLE_DRIVE_FOLDER_ID:
        print("❌ Google Drive folder ID not configured")
        return False
    else:
        print(f"✓ Folder ID: {config.GOOGLE_DRIVE_FOLDER_ID}")
    
    # Test authentication
    print("\n3. Testing Google Drive authentication...")
    print("   (A browser window will open for authentication)")
    
    try:
        handler = GoogleDriveHandler()
        print("✓ Authentication successful!")
        
        # List files in the folder
        print("\n4. Testing file listing...")
        files = handler.list_pdf_files(max_results=10)
        
        if files:
            print(f"✓ Found {len(files)} PDF files in the folder")
            print("\nFirst 5 files:")
            for i, file in enumerate(files[:5], 1):
                size_mb = int(file.get('size', 0)) / (1024 * 1024)
                print(f"   {i}. {file['name']} ({size_mb:.2f} MB)")
        else:
            print("⚠ No PDF files found in the folder")
        
        print("\n" + "=" * 70)
        print("✓ Google Drive API Setup Complete!")
        print("=" * 70)
        print("\nYou can now use the following commands:")
        print("  python main.py --sync              # Sync files from Drive")
        print("  python main.py --process           # Process PDF files")
        print("  python main.py --stats             # View statistics")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure client.json is valid OAuth 2.0 credentials")
        print("2. Ensure Google Drive API is enabled in Google Cloud Console")
        print("3. Check that the folder ID is correct and accessible")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

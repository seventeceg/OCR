"""
Google Drive Handler for downloading and managing PDF files
Optimized for handling 100K+ files with batch downloading
"""
import os
import pickle
from pathlib import Path
from typing import List, Dict, Optional
import time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from loguru import logger
import io

import config

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']


class GoogleDriveHandler:
    """Handler for Google Drive operations"""
    
    def __init__(self):
        self.service = None
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with Google Drive API"""
        creds = None
        
        # Load saved credentials
        if os.path.exists(config.GOOGLE_TOKEN_PATH):
            with open(config.GOOGLE_TOKEN_PATH, 'rb') as token:
                creds = pickle.load(token)
        
        # If no valid credentials, authenticate
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(config.GOOGLE_CREDENTIALS_PATH):
                    raise FileNotFoundError(
                        f"Credentials file not found: {config.GOOGLE_CREDENTIALS_PATH}\n"
                        "Please download it from Google Cloud Console"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    config.GOOGLE_CREDENTIALS_PATH, SCOPES
                )
                creds = flow.run_local_server(port=0)
            
            # Save credentials
            with open(config.GOOGLE_TOKEN_PATH, 'wb') as token:
                pickle.dump(creds, token)
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("✓ Authenticated with Google Drive")
    
    def list_pdf_files(self, folder_id: Optional[str] = None, 
                       max_results: int = 1000) -> List[Dict]:
        """
        List all PDF files in Google Drive folder
        
        Args:
            folder_id: Google Drive folder ID (from config if None)
            max_results: Maximum number of results per page
            
        Returns:
            List of file metadata dictionaries
        """
        if folder_id is None:
            folder_id = config.GOOGLE_DRIVE_FOLDER_ID
        
        if not folder_id:
            raise ValueError("Google Drive folder ID not configured")
        
        logger.info(f"Listing PDF files from folder: {folder_id}")
        
        files = []
        page_token = None
        
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        
        try:
            while True:
                results = self.service.files().list(
                    q=query,
                    pageSize=max_results,
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, size, createdTime, modifiedTime, parents)"
                ).execute()
                
                batch_files = results.get('files', [])
                files.extend(batch_files)
                
                logger.info(f"Retrieved {len(batch_files)} files (Total: {len(files)})")
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                
                # Small delay to avoid rate limiting
                time.sleep(0.1)
            
            logger.info(f"✓ Total PDF files found: {len(files)}")
            return files
            
        except Exception as e:
            logger.error(f"Error listing files: {e}")
            raise
    
    def download_file(self, file_id: str, filename: str, 
                     output_dir: Path = None) -> Path:
        """
        Download a file from Google Drive
        
        Args:
            file_id: Google Drive file ID
            filename: Name of the file
            output_dir: Output directory (uses INPUT_DIR if None)
            
        Returns:
            Path to downloaded file
        """
        if output_dir is None:
            output_dir = config.INPUT_DIR
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_path = output_dir / filename
        
        # Skip if already downloaded
        if output_path.exists():
            logger.debug(f"File already exists: {filename}")
            return output_path
        
        try:
            request = self.service.files().get_media(fileId=file_id)
            
            with io.FileIO(str(output_path), 'wb') as fh:
                downloader = MediaIoBaseDownload(fh, request)
                done = False
                
                while not done:
                    status, done = downloader.next_chunk()
                    if status:
                        progress = int(status.progress() * 100)
                        if progress % 25 == 0:  # Log every 25%
                            logger.debug(f"Downloading {filename}: {progress}%")
            
            logger.info(f"✓ Downloaded: {filename}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            if output_path.exists():
                output_path.unlink()  # Remove partial download
            raise
    
    def batch_download_files(self, file_list: List[Dict], 
                           output_dir: Path = None,
                           max_concurrent: int = 5) -> List[Path]:
        """
        Download multiple files with error handling
        
        Args:
            file_list: List of file metadata dictionaries
            output_dir: Output directory
            max_concurrent: Maximum concurrent downloads (not implemented yet)
            
        Returns:
            List of successfully downloaded file paths
        """
        downloaded_files = []
        failed_files = []
        
        total_files = len(file_list)
        logger.info(f"Starting batch download of {total_files} files")
        
        for idx, file_info in enumerate(file_list, 1):
            file_id = file_info['id']
            filename = file_info['name']
            
            try:
                logger.info(f"[{idx}/{total_files}] Downloading: {filename}")
                path = self.download_file(file_id, filename, output_dir)
                downloaded_files.append(path)
                
            except Exception as e:
                logger.error(f"Failed to download {filename}: {e}")
                failed_files.append({'file': filename, 'error': str(e)})
                continue
        
        logger.info(f"✓ Downloaded: {len(downloaded_files)}/{total_files}")
        if failed_files:
            logger.warning(f"✗ Failed: {len(failed_files)} files")
        
        return downloaded_files
    
    def get_file_metadata(self, file_id: str) -> Dict:
        """Get metadata for a specific file"""
        try:
            file = self.service.files().get(
                fileId=file_id,
                fields='id, name, size, mimeType, createdTime, modifiedTime'
            ).execute()
            return file
        except Exception as e:
            logger.error(f"Error getting file metadata: {e}")
            raise
    
    def stream_file_list(self, folder_id: Optional[str] = None, 
                        chunk_size: int = 100):
        """
        Generator that yields file lists in chunks
        Useful for processing 100K+ files without loading all into memory
        
        Args:
            folder_id: Google Drive folder ID
            chunk_size: Number of files per chunk
            
        Yields:
            Lists of file metadata
        """
        if folder_id is None:
            folder_id = config.GOOGLE_DRIVE_FOLDER_ID
        
        query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
        page_token = None
        chunk = []
        
        while True:
            try:
                results = self.service.files().list(
                    q=query,
                    pageSize=min(chunk_size, 1000),
                    pageToken=page_token,
                    fields="nextPageToken, files(id, name, size, createdTime, modifiedTime)"
                ).execute()
                
                files = results.get('files', [])
                chunk.extend(files)
                
                # Yield chunk when it reaches desired size
                if len(chunk) >= chunk_size:
                    yield chunk
                    chunk = []
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    # Yield remaining files
                    if chunk:
                        yield chunk
                    break
                
                time.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Error streaming file list: {e}")
                raise


def test_connection():
    """Test Google Drive connection"""
    try:
        handler = GoogleDriveHandler()
        logger.info("✓ Google Drive connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Google Drive connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test connection
    test_connection()

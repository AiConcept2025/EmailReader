#!/usr/bin/env python3
"""
Simple script to upload files to Google Drive with translation properties.
"""
import argparse
import uuid
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.google_drive import GoogleApi


def main():
    parser = argparse.ArgumentParser(
        description='Upload file to Google Drive for translation'
    )
    parser.add_argument('file_name', help='Path to the file to upload')
    parser.add_argument(
        'translation_mode',
        help='Translation mode (e.g., default, human, formats)'
    )
    args = parser.parse_args()

    # Validate file exists
    if not os.path.exists(args.file_name):
        print(f"Error: File not found: {args.file_name}")
        sys.exit(1)

    # Initialize Google API
    print("Initializing Google Drive API...")
    google_api = GoogleApi()
    parent_folder_id = google_api.parent_folder_id

    # Verify/create folder structure: danishevsky@yahoo.com/Inbox
    email_folder = "danishevsky@yahoo.com"
    inbox_folder = "Inbox"

    print(f"Verifying folder structure: {email_folder}/{inbox_folder}")

    # Check if email folder exists
    if not google_api.if_folder_exist_by_name(
            folder_name=email_folder,
            parent_folder_id=parent_folder_id):
        print(f"Creating folder: {email_folder}")
        result = google_api.create_subfolder_in_folder(
            folder_name=email_folder,
            parent_folder_id=parent_folder_id
        )
        email_folder_id = result.get('id', '')
        if not email_folder_id:
            print(f"Error: Failed to create folder {email_folder}")
            sys.exit(1)
    else:
        # Get email folder ID
        subfolders = google_api.get_subfolders_list_in_folder(
            parent_folder_id=parent_folder_id
        )
        email_folder_obj = next(
            (f for f in subfolders if f['name'] == email_folder), None
        )
        if not email_folder_obj:
            print(f"Error: Could not find folder {email_folder}")
            sys.exit(1)
        email_folder_id = email_folder_obj['id']

    print(f"Email folder ID: {email_folder_id}")

    # Check if Inbox subfolder exists
    if not google_api.if_folder_exist_by_name(
            folder_name=inbox_folder,
            parent_folder_id=email_folder_id):
        print(f"Creating subfolder: {inbox_folder}")
        result = google_api.create_subfolder_in_folder(
            folder_name=inbox_folder,
            parent_folder_id=email_folder_id
        )
        inbox_folder_id = result.get('id', '')
        if not inbox_folder_id:
            print(f"Error: Failed to create subfolder {inbox_folder}")
            sys.exit(1)
    else:
        # Get Inbox folder ID
        subfolders = google_api.get_subfolders_list_in_folder(
            parent_folder_id=email_folder_id
        )
        inbox_folder_obj = next(
            (f for f in subfolders if f['name'] == inbox_folder), None
        )
        if not inbox_folder_obj:
            print(f"Error: Could not find subfolder {inbox_folder}")
            sys.exit(1)
        inbox_folder_id = inbox_folder_obj['id']

    print(f"Inbox folder ID: {inbox_folder_id}")

    # Generate transaction ID
    transaction_id = str(uuid.uuid4())

    # Prepare properties
    properties = {
        'source_language': 'ru',
        'target_language': 'en',
        'translation_mode': args.translation_mode,
        'transaction_id': transaction_id
    }

    # Upload file
    file_name = os.path.basename(args.file_name)
    print(f"\nUploading file: {file_name}")
    print(f"Translation mode: {args.translation_mode}")
    print(f"Transaction ID: {transaction_id}")

    file_info = google_api.upload_file_to_google_drive(
        file_path=args.file_name,
        file_name=file_name,
        parent_folder_id=inbox_folder_id,
        description=f"Uploaded via upload_file.py (mode: {args.translation_mode})",
        properties=properties
    )

    file_id = file_info.get('id', None)
    if not file_id:
        print("\nError: Upload failed")
        sys.exit(1)

    # Get file URL
    file_url = google_api.get_file_web_link(file_id)

    print("\n" + "="*60)
    print("Upload successful!")
    print("="*60)
    print(f"File Name: {file_name}")
    print(f"File ID: {file_id}")
    print(f"File URL: {file_url}")
    print(f"Location: {email_folder}/{inbox_folder}")
    print(f"Transaction ID: {transaction_id}")
    print("="*60)


if __name__ == '__main__':
    main()

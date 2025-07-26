#!/usr/bin/env python3
"""
Simple debug script for testing Google Drive file operations
Run with: python test_google_drive_debug.py
Or in debugger: python -m pdb test_google_drive_debug.py
"""

import os
import sys
from src.google_drive import GoogleApi
from src.logger import logger


def test_google_drive_operations():
    """Test Google Drive operations with detailed output"""

    print("=== Google Drive Debug Test ===\n")

    # Initialize Google Drive API
    try:
        google_api = GoogleApi()
        print("✓ Google Drive API initialized successfully")
        print(f"  Parent folder ID: {google_api.parent_folder_id}\n")
    except Exception as e:
        print(f"✗ Failed to initialize Google Drive API: {e}")
        return

    # 1. List folders in parent
    print("1. Listing folders in parent directory...")
    try:
        folders = google_api.get_folders_list()
        print(f"   Found {len(folders)} folders:")
        for folder in folders[:5]:  # Show first 5
            print(f"   - {folder['name']} (ID: {folder['id']})")
        if len(folders) > 5:
            print(f"   ... and {len(folders) - 5} more")
        print()
    except Exception as e:
        print(f"✗ Error listing folders: {e}\n")
        return

    # 2. Find a test folder with inbox
    test_folder = None
    inbox_folder = None

    if folders:
        # Use first folder as test
        test_folder = folders[0]
        print(f"2. Using test folder: {test_folder['name']}")

        # Look for inbox subfolder
        try:
            subfolders = google_api.get_folders_list(
                parent_folder_id=test_folder['id'])
            for sub in subfolders:
                if sub['name'] == 'inbox':
                    inbox_folder = sub
                    print(f"   Found inbox folder (ID: {inbox_folder['id']})")
                    break
        except Exception as e:
            print(f"✗ Error getting subfolders: {e}")

    # 3. List files in inbox
    if inbox_folder:
        print(f"\n3. Listing files in inbox...")
        try:
            files = google_api.get_file_list_in_folder(
                parent_folder_id=inbox_folder['id'])
            print(f"   Found {len(files)} files:")

            test_file = None
            for file in files[:5]:  # Show first 5
                print(f"   - {file['name']} (ID: {file['id']})")
                if not test_file:
                    test_file = file  # Use first file for testing

            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more")
            print()

            # 4. Test delete operation on first file
            if test_file:
                print(f"4. Testing delete operation on: {test_file['name']}")
                print(f"   File ID: {test_file['id']}")

                # Add diagnostic check
                print("\n   Checking file permissions...")
                try:
                    file_info = google_api.service.files().get(
                        fileId=test_file['id'],
                        fields='id,name,parents,ownedByMe,trashed,capabilities',
                        supportsAllDrives=True
                    ).execute()

                    print(
                        f"   - Owned by me: {file_info.get('ownedByMe', False)}")
                    print(
                        f"   - Already trashed: {file_info.get('trashed', False)}")

                    capabilities = file_info.get('capabilities', {})
                    print(
                        f"   - Can trash: {capabilities.get('canTrash', False)}")
                    print(
                        f"   - Can delete: {capabilities.get('canDelete', False)}")
                    print(
                        f"   - Can edit: {capabilities.get('canEdit', False)}")

                except Exception as e:
                    print(f"   ✗ Error checking permissions: {e}")

                # Try to delete
                print("\n   Attempting to trash file...")
                result = google_api.delete_file(file_id=test_file['id'])

                if result:
                    print("   ✓ File trashed successfully!")
                    print(f"   Response: {result}")
                else:
                    print("   ✗ Failed to trash file")

                    # Try alternative: move to a different folder
                    print(
                        "\n   Trying alternative: Create a 'deleted' folder and move file there...")
                    try:
                        # Create or find deleted folder
                        deleted_folder = google_api.create_subfolder_in_folder(
                            folder_name='deleted',
                            parent_folder_id=test_folder['id']
                        )
                        if deleted_folder.id:
                            print(
                                f"   Created/found 'deleted' folder: {deleted_folder.id}")

                            # Try to move file
                            print(
                                "   Attempting to move file to 'deleted' folder...")
                            # Add move operation here if needed
                    except Exception as e:
                        print(f"   ✗ Alternative approach failed: {e}")
            else:
                print("No files found to test delete operation")
        except Exception as e:
            print(f"✗ Error listing files: {e}")
    else:
        print("No inbox folder found")

    print("\n=== Test Complete ===")


def test_specific_file(file_id):
    """Test operations on a specific file by ID"""
    print(f"\n=== Testing specific file: {file_id} ===")

    google_api = GoogleApi()

    # Get file info
    try:
        file_info = google_api.service.files().get(
            fileId=file_id,
            fields='*',
            supportsAllDrives=True
        ).execute()

        print(f"File: {file_info.get('name')}")
        print(f"MIME Type: {file_info.get('mimeType')}")
        print(f"Parents: {file_info.get('parents', [])}")
        print(f"Owned by me: {file_info.get('ownedByMe', False)}")
        print(f"Trashed: {file_info.get('trashed', False)}")

        # Try delete
        print("\nAttempting delete...")
        result = google_api.delete_file(file_id=file_id)
        if result:
            print("✓ Success!")
        else:
            print("✗ Failed")

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    # Check if a specific file ID was provided
    if len(sys.argv) > 1:
        test_specific_file(sys.argv[1])
    else:
        test_google_drive_operations()

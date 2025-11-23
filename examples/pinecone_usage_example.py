"""
Example usage of PineconeAssistant class methods.

This script demonstrates how to use all the methods in the PineconeAssistant class
for document management and querying with Pinecone.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pinecone_utils import PineconeAssistant


def main():
    """Demonstrate PineconeAssistant usage."""

    # Initialize the assistant
    print("Initializing Pinecone Assistant...")
    try:
        assistant = PineconeAssistant()
        print("✓ Assistant initialized successfully\n")
    except Exception as e:
        print(f"✗ Failed to initialize: {e}")
        return

    # Example 1: Upload a file
    print("=" * 60)
    print("Example 1: Upload a file")
    print("=" * 60)
    file_path = "path/to/document.pdf"
    metadata = {
        "client_email": "user@example.com",
        "document_type": "invoice",
        "created_by": "system"
    }

    print(f"Uploading file: {file_path}")
    print(f"Metadata: {metadata}")
    try:
        # Uncomment to actually upload:
        # file_id = assistant.upload_file(file_path=file_path, metadata=metadata)
        # print(f"✓ File uploaded successfully! ID: {file_id}\n")

        # For demo purposes, using a placeholder
        file_id = "demo-file-123"
        print(f"(Demo mode) File ID: {file_id}\n")
    except Exception as e:
        print(f"✗ Upload failed: {e}\n")

    # Example 2: List all files
    print("=" * 60)
    print("Example 2: List all files")
    print("=" * 60)
    try:
        # Uncomment to actually list:
        # files = assistant.list_files(limit=10)
        # print(f"✓ Found {len(files)} file(s):")
        # for file in files:
        #     print(f"  - {file.name} (ID: {file.id}, Status: {file.status})")
        # print()

        print("(Demo mode) Files would be listed here\n")
    except Exception as e:
        print(f"✗ Failed to list files: {e}\n")

    # Example 3: List files with filter
    print("=" * 60)
    print("Example 3: List files with metadata filter")
    print("=" * 60)
    filter_criteria = {"client_email": "user@example.com"}
    print(f"Filter: {filter_criteria}")
    try:
        # Uncomment to actually list:
        # files = assistant.list_files(filter=filter_criteria, limit=10)
        # print(f"✓ Found {len(files)} matching file(s)\n")

        print("(Demo mode) Filtered files would be listed here\n")
    except Exception as e:
        print(f"✗ Failed to list files: {e}\n")

    # Example 4: Get file metadata
    print("=" * 60)
    print("Example 4: Get file metadata")
    print("=" * 60)
    print(f"Fetching metadata for file ID: {file_id}")
    try:
        # Uncomment to actually fetch:
        # metadata_result = assistant.get_file_metadata(file_id=file_id)
        # print("✓ File metadata retrieved:")
        # print(f"  Name: {metadata_result['name']}")
        # print(f"  Status: {metadata_result['status']}")
        # print(f"  Size: {metadata_result['size']} bytes")
        # print(f"  Progress: {metadata_result['percent_done'] * 100:.1f}%")
        # print(f"  Metadata: {metadata_result['metadata']}")
        # print()

        print("(Demo mode) Metadata would be displayed here\n")
    except Exception as e:
        print(f"✗ Failed to get metadata: {e}\n")

    # Example 5: Query documents
    print("=" * 60)
    print("Example 5: Query documents")
    print("=" * 60)
    query = "What is the total amount on the invoice?"
    print(f"Query: '{query}'")
    print(f"Filter: {filter_criteria}")
    try:
        # Uncomment to actually query:
        # results = assistant.query_documents(
        #     query_text=query,
        #     top_k=5,
        #     filter=filter_criteria
        # )
        # print("✓ Query results retrieved")
        # print(f"  Number of results: {len(results.get('chunks', []))}")
        # print()

        print("(Demo mode) Query results would be displayed here\n")
    except Exception as e:
        print(f"✗ Query failed: {e}\n")

    # Example 6: Chat with the assistant
    print("=" * 60)
    print("Example 6: Chat with the assistant")
    print("=" * 60)
    messages = [
        {"role": "user", "content": "Summarize the uploaded invoice"}
    ]
    print(f"Messages: {messages}")
    try:
        # Uncomment to actually chat:
        # response = assistant.chat(
        #     messages=messages,
        #     filter=filter_criteria
        # )
        # print("✓ Chat response received:")
        # print(f"  {response.message.content}")
        # print()

        print("(Demo mode) Chat response would be displayed here\n")
    except Exception as e:
        print(f"✗ Chat failed: {e}\n")

    # Example 7: Update metadata (will raise NotImplementedError)
    print("=" * 60)
    print("Example 7: Update metadata (demonstrates API limitation)")
    print("=" * 60)
    new_metadata = {"status": "processed", "reviewed": True}
    print(f"Attempting to update metadata to: {new_metadata}")
    try:
        # This will raise NotImplementedError
        assistant.update_metadata(file_id=file_id, metadata=new_metadata)
    except NotImplementedError as e:
        print(f"✓ Expected limitation encountered: {e}\n")
    except Exception as e:
        print(f"✗ Unexpected error: {e}\n")

    # Example 8: Delete a file
    print("=" * 60)
    print("Example 8: Delete a file")
    print("=" * 60)
    print(f"Deleting file ID: {file_id}")
    try:
        # Uncomment to actually delete:
        # assistant.delete_file(file_id=file_id)
        # print("✓ File deleted successfully\n")

        print("(Demo mode) File would be deleted here\n")
    except Exception as e:
        print(f"✗ Deletion failed: {e}\n")

    print("=" * 60)
    print("Demo completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

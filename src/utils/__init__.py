"""Utilities module for EmailReader."""

# Import from sibling utils.py module
import importlib.util
import sys
from pathlib import Path

# Load utils.py as a separate module
utils_file = Path(__file__).parent.parent / 'utils.py'
spec = importlib.util.spec_from_file_location("_parent_utils", utils_file)
if spec and spec.loader:
    _parent_utils = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_parent_utils)

    # Re-export all public functions
    read_json_secret_file = _parent_utils.read_json_secret_file
    list_all_dir_files = _parent_utils.list_all_dir_files
    list_files_in_directory = _parent_utils.list_files_in_directory
    get_uuid = _parent_utils.get_uuid
    read_pdf_doc_to_text = _parent_utils.read_pdf_doc_to_text
    read_word_doc_to_text = _parent_utils.read_word_doc_to_text
    translate_document_to_english = _parent_utils.translate_document_to_english
    copy_file = _parent_utils.copy_file
    delete_file = _parent_utils.delete_file
    rename_file = _parent_utils.rename_file
    convert_rtx_to_text = _parent_utils.convert_rtx_to_text
    utc_to_local = _parent_utils.utc_to_local
    build_flowise_question = _parent_utils.build_flowise_question
    verify_paragraph_counts = _parent_utils.verify_paragraph_counts

    __all__ = [
        'read_json_secret_file', 'list_all_dir_files', 'list_files_in_directory',
        'get_uuid', 'read_pdf_doc_to_text', 'read_word_doc_to_text',
        'translate_document_to_english', 'copy_file', 'delete_file', 'rename_file',
        'convert_rtx_to_text', 'utc_to_local', 'build_flowise_question', 'verify_paragraph_counts'
    ]

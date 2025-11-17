"""Utilities module for EmailReader."""

# Import functions from src.utils module (utils.py file) to maintain backwards compatibility
# This allows "from src.utils import func" to work even though utils is now a package
import importlib.util
import sys
from pathlib import Path

# Get the path to utils.py (sibling to this utils/ directory)
utils_py_path = Path(__file__).parent.parent / "utils.py"

# Load the module directly from the file
spec = importlib.util.spec_from_file_location("_src_utils_module", utils_py_path)
if spec and spec.loader:
    _utils_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_utils_module)

    # Import all public functions from the utils.py module
    delete_file = _utils_module.delete_file
    translate_document_to_english = _utils_module.translate_document_to_english
    convert_rtx_to_text = _utils_module.convert_rtx_to_text
    rename_file = _utils_module.rename_file
    read_json_secret_file = _utils_module.read_json_secret_file
    list_all_dir_files = _utils_module.list_all_dir_files
    list_files_in_directory = _utils_module.list_files_in_directory
    get_uuid = _utils_module.get_uuid
    read_pdf_doc_to_text = _utils_module.read_pdf_doc_to_text
    read_word_doc_to_text = _utils_module.read_word_doc_to_text
    copy_file = _utils_module.copy_file
    utc_to_local = _utils_module.utc_to_local
    build_flowise_question = _utils_module.build_flowise_question

    # Re-export all imported functions
    __all__ = [
        'delete_file',
        'translate_document_to_english',
        'convert_rtx_to_text',
        'rename_file',
        'read_json_secret_file',
        'list_all_dir_files',
        'list_files_in_directory',
        'get_uuid',
        'read_pdf_doc_to_text',
        'read_word_doc_to_text',
        'copy_file',
        'utc_to_local',
        'build_flowise_question'
    ]

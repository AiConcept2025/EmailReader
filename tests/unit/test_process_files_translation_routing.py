"""
Unit tests for translation routing in process_files_for_translation.py.

Tests that translate_file() routes to the correct translator provider
based on translation_mode from file metadata.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock, call
from src.process_files_for_translation import translate_file


class TestTranslationRouting:
    """Test translation provider routing based on translation_mode."""

    @pytest.mark.asyncio
    @patch('src.process_files_for_translation.google_api')
    @patch('src.process_files_for_translation.load_config')
    @patch('src.translation.TranslatorFactory')
    @patch('src.process_files_for_translation.convert_to_docx_for_translation')
    @patch('src.process_files_for_translation.delete_file')
    @patch('src.process_files_for_translation.requests')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.path.join')
    async def test_human_mode_routes_to_google_batch(
        self, mock_join, mock_getsize, mock_exists, mock_requests,
        mock_delete, mock_convert, mock_factory, mock_load_config, mock_google_api
    ):
        """Test that translation_mode='human' routes to google_batch provider."""
        # Setup mock config
        mock_config = {
            'translation': {
                'provider': 'google_doc',  # Default provider
                'google_doc': {
                    'project_id': 'test-project'
                }
            },
            'app': {
                'translator_url': 'http://test.com/webhook'
            }
        }
        mock_load_config.return_value = mock_config

        # Setup file with human translation mode
        test_file = {
            'name': 'test.pdf',
            'id': 'file123',
            'properties': {
                'translation_mode': 'human',
                'target_language': 'fr',
                'source_language': 'en',
                'transaction_id': 'txn123'
            },
            'description': 'Test file'
        }

        # Setup mocks
        mock_google_api.download_file_from_google_drive.return_value = True
        mock_google_api.move_file_to_folder_id.return_value = True
        mock_google_api.upload_file_to_google_drive.return_value = {'id': 'uploaded123'}
        mock_google_api.get_file_web_link.return_value = 'http://test.com/file'
        mock_google_api.get_file_parent_folder_id.return_value = 'parent123'
        mock_google_api.get_folder_name_by_id.return_value = 'TestCompany'

        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_translator = MagicMock()
        mock_factory.get_translator.return_value = mock_translator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Call the function
        await translate_file(
            fl=test_file,
            client_email='test@example.com',
            inbox_folder='/inbox',
            completed_id='completed123',
            completed_folder='/completed',
            client_folder_id='client123',
            translate_folder_id='translate123',
            url='http://test.com/webhook'
        )

        # Verify load_config was called
        assert mock_load_config.called

        # Verify config was modified to use google_batch for human mode
        # The function should modify the config before calling TranslatorFactory
        factory_call_args = mock_factory.get_translator.call_args
        config_passed = factory_call_args[0][0]

        assert config_passed['translation']['provider'] == 'google_batch'

    @pytest.mark.asyncio
    @patch('src.process_files_for_translation.google_api')
    @patch('src.process_files_for_translation.load_config')
    @patch('src.translation.TranslatorFactory')
    @patch('src.process_files_for_translation.convert_to_docx_for_translation')
    @patch('src.process_files_for_translation.delete_file')
    @patch('src.process_files_for_translation.requests')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.path.join')
    async def test_default_mode_uses_configured_provider(
        self, mock_join, mock_getsize, mock_exists, mock_requests,
        mock_delete, mock_convert, mock_factory, mock_load_config, mock_google_api
    ):
        """Test that translation_mode='default' uses the configured provider."""
        # Setup mock config with google_doc as provider
        mock_config = {
            'translation': {
                'provider': 'google_doc',
                'google_doc': {
                    'project_id': 'test-project'
                }
            },
            'app': {
                'translator_url': 'http://test.com/webhook'
            }
        }
        mock_load_config.return_value = mock_config

        # Setup file with default translation mode
        test_file = {
            'name': 'test.pdf',
            'id': 'file123',
            'properties': {
                'translation_mode': 'default',
                'target_language': 'fr',
                'source_language': 'en',
                'transaction_id': 'txn123'
            },
            'description': 'Test file'
        }

        # Setup mocks
        mock_google_api.download_file_from_google_drive.return_value = True
        mock_google_api.move_file_to_folder_id.return_value = True
        mock_google_api.upload_file_to_google_drive.return_value = {'id': 'uploaded123'}
        mock_google_api.get_file_web_link.return_value = 'http://test.com/file'
        mock_google_api.get_file_parent_folder_id.return_value = 'parent123'
        mock_google_api.get_folder_name_by_id.return_value = 'TestCompany'

        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_translator = MagicMock()
        mock_factory.get_translator.return_value = mock_translator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Call the function
        await translate_file(
            fl=test_file,
            client_email='test@example.com',
            inbox_folder='/inbox',
            completed_id='completed123',
            completed_folder='/completed',
            client_folder_id='client123',
            translate_folder_id='translate123',
            url='http://test.com/webhook'
        )

        # Verify config provider was NOT changed
        factory_call_args = mock_factory.get_translator.call_args
        config_passed = factory_call_args[0][0]

        assert config_passed['translation']['provider'] == 'google_doc'

    @pytest.mark.asyncio
    @patch('src.process_files_for_translation.google_api')
    @patch('src.process_files_for_translation.load_config')
    @patch('src.translation.TranslatorFactory')
    @patch('src.process_files_for_translation.convert_to_docx_for_translation')
    @patch('src.process_files_for_translation.delete_file')
    @patch('src.process_files_for_translation.requests')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.path.join')
    async def test_formats_mode_uses_configured_provider(
        self, mock_join, mock_getsize, mock_exists, mock_requests,
        mock_delete, mock_convert, mock_factory, mock_load_config, mock_google_api
    ):
        """Test that translation_mode='formats' uses the configured provider."""
        # Setup mock config
        mock_config = {
            'translation': {
                'provider': 'google_text',
                'google_text': {
                    'path': '/usr/bin/translate'
                }
            },
            'app': {
                'translator_url': 'http://test.com/webhook'
            }
        }
        mock_load_config.return_value = mock_config

        # Setup file with formats translation mode
        test_file = {
            'name': 'test.pdf',
            'id': 'file123',
            'properties': {
                'translation_mode': 'formats',
                'target_language': 'de',
                'source_language': 'en',
                'transaction_id': 'txn123'
            },
            'description': 'Test file'
        }

        # Setup mocks
        mock_google_api.download_file_from_google_drive.return_value = True
        mock_google_api.move_file_to_folder_id.return_value = True
        mock_google_api.upload_file_to_google_drive.return_value = {'id': 'uploaded123'}
        mock_google_api.get_file_web_link.return_value = 'http://test.com/file'
        mock_google_api.get_file_parent_folder_id.return_value = 'parent123'
        mock_google_api.get_folder_name_by_id.return_value = 'TestCompany'

        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_translator = MagicMock()
        mock_factory.get_translator.return_value = mock_translator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Call the function
        await translate_file(
            fl=test_file,
            client_email='test@example.com',
            inbox_folder='/inbox',
            completed_id='completed123',
            completed_folder='/completed',
            client_folder_id='client123',
            translate_folder_id='translate123',
            url='http://test.com/webhook'
        )

        # Verify config provider was NOT changed
        factory_call_args = mock_factory.get_translator.call_args
        config_passed = factory_call_args[0][0]

        assert config_passed['translation']['provider'] == 'google_text'

    @pytest.mark.asyncio
    @patch('src.process_files_for_translation.google_api')
    @patch('src.process_files_for_translation.load_config')
    @patch('src.translation.TranslatorFactory')
    @patch('src.process_files_for_translation.convert_to_docx_for_translation')
    @patch('src.process_files_for_translation.delete_file')
    @patch('src.process_files_for_translation.requests')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.path.join')
    async def test_missing_translation_mode_defaults_to_configured_provider(
        self, mock_join, mock_getsize, mock_exists, mock_requests,
        mock_delete, mock_convert, mock_factory, mock_load_config, mock_google_api
    ):
        """Test that missing translation_mode uses the configured provider."""
        # Setup mock config
        mock_config = {
            'translation': {
                'provider': 'google_doc',
                'google_doc': {
                    'project_id': 'test-project'
                }
            },
            'app': {
                'translator_url': 'http://test.com/webhook'
            }
        }
        mock_load_config.return_value = mock_config

        # Setup file WITHOUT translation_mode property
        test_file = {
            'name': 'test.pdf',
            'id': 'file123',
            'properties': {
                'target_language': 'es',
                'source_language': 'en',
                'transaction_id': 'txn123'
            },
            'description': 'Test file'
        }

        # Setup mocks
        mock_google_api.download_file_from_google_drive.return_value = True
        mock_google_api.move_file_to_folder_id.return_value = True
        mock_google_api.upload_file_to_google_drive.return_value = {'id': 'uploaded123'}
        mock_google_api.get_file_web_link.return_value = 'http://test.com/file'
        mock_google_api.get_file_parent_folder_id.return_value = 'parent123'
        mock_google_api.get_folder_name_by_id.return_value = 'TestCompany'

        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_translator = MagicMock()
        mock_factory.get_translator.return_value = mock_translator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Call the function
        await translate_file(
            fl=test_file,
            client_email='test@example.com',
            inbox_folder='/inbox',
            completed_id='completed123',
            completed_folder='/completed',
            client_folder_id='client123',
            translate_folder_id='translate123',
            url='http://test.com/webhook'
        )

        # Verify config provider was NOT changed (defaults to 'default' mode)
        factory_call_args = mock_factory.get_translator.call_args
        config_passed = factory_call_args[0][0]

        assert config_passed['translation']['provider'] == 'google_doc'

    @pytest.mark.asyncio
    @patch('src.process_files_for_translation.google_api')
    @patch('src.process_files_for_translation.load_config')
    @patch('src.translation.TranslatorFactory')
    @patch('src.process_files_for_translation.convert_to_docx_for_translation')
    @patch('src.process_files_for_translation.delete_file')
    @patch('src.process_files_for_translation.requests')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.path.join')
    async def test_human_mode_handles_missing_translation_key_in_config(
        self, mock_join, mock_getsize, mock_exists, mock_requests,
        mock_delete, mock_convert, mock_factory, mock_load_config, mock_google_api
    ):
        """Test that human mode gracefully handles missing translation key in config."""
        # Setup mock config WITHOUT translation key
        mock_config = {
            'app': {
                'translator_url': 'http://test.com/webhook'
            }
        }
        mock_load_config.return_value = mock_config

        # Setup file with human translation mode
        test_file = {
            'name': 'test.pdf',
            'id': 'file123',
            'properties': {
                'translation_mode': 'human',
                'target_language': 'fr',
                'source_language': 'en',
                'transaction_id': 'txn123'
            },
            'description': 'Test file'
        }

        # Setup mocks
        mock_google_api.download_file_from_google_drive.return_value = True
        mock_google_api.move_file_to_folder_id.return_value = True
        mock_google_api.upload_file_to_google_drive.return_value = {'id': 'uploaded123'}
        mock_google_api.get_file_web_link.return_value = 'http://test.com/file'
        mock_google_api.get_file_parent_folder_id.return_value = 'parent123'
        mock_google_api.get_folder_name_by_id.return_value = 'TestCompany'

        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_translator = MagicMock()
        mock_factory.get_translator.return_value = mock_translator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Call the function
        await translate_file(
            fl=test_file,
            client_email='test@example.com',
            inbox_folder='/inbox',
            completed_id='completed123',
            completed_folder='/completed',
            client_folder_id='client123',
            translate_folder_id='translate123',
            url='http://test.com/webhook'
        )

        # Verify translation key was created with google_batch provider
        factory_call_args = mock_factory.get_translator.call_args
        config_passed = factory_call_args[0][0]

        assert 'translation' in config_passed
        assert config_passed['translation']['provider'] == 'google_batch'

    @pytest.mark.asyncio
    @patch('src.process_files_for_translation.google_api')
    @patch('src.process_files_for_translation.load_config')
    @patch('src.translation.TranslatorFactory')
    @patch('src.process_files_for_translation.logger')
    @patch('src.process_files_for_translation.convert_to_docx_for_translation')
    @patch('src.process_files_for_translation.delete_file')
    @patch('src.process_files_for_translation.requests')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('os.path.join')
    async def test_human_mode_logs_batch_translator_selection(
        self, mock_join, mock_getsize, mock_exists, mock_requests,
        mock_delete, mock_convert, mock_logger, mock_factory,
        mock_load_config, mock_google_api
    ):
        """Test that human mode logs the selection of batch translator."""
        # Setup mock config
        mock_config = {
            'translation': {
                'provider': 'google_doc',
                'google_doc': {
                    'project_id': 'test-project'
                }
            },
            'app': {
                'translator_url': 'http://test.com/webhook'
            }
        }
        mock_load_config.return_value = mock_config

        # Setup file with human translation mode
        test_file = {
            'name': 'test.pdf',
            'id': 'file123',
            'properties': {
                'translation_mode': 'human',
                'target_language': 'fr',
                'source_language': 'en',
                'transaction_id': 'txn123'
            },
            'description': 'Test file'
        }

        # Setup mocks
        mock_google_api.download_file_from_google_drive.return_value = True
        mock_google_api.move_file_to_folder_id.return_value = True
        mock_google_api.upload_file_to_google_drive.return_value = {'id': 'uploaded123'}
        mock_google_api.get_file_web_link.return_value = 'http://test.com/file'
        mock_google_api.get_file_parent_folder_id.return_value = 'parent123'
        mock_google_api.get_folder_name_by_id.return_value = 'TestCompany'

        mock_join.side_effect = lambda *args: '/'.join(args)
        mock_exists.return_value = True
        mock_getsize.return_value = 1024

        mock_translator = MagicMock()
        mock_factory.get_translator.return_value = mock_translator

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        # Call the function
        await translate_file(
            fl=test_file,
            client_email='test@example.com',
            inbox_folder='/inbox',
            completed_id='completed123',
            completed_folder='/completed',
            client_folder_id='client123',
            translate_folder_id='translate123',
            url='http://test.com/webhook'
        )

        # Verify logger was called with appropriate message
        # Look for a log message about using batch translator
        log_calls = [str(call) for call in mock_logger.info.call_args_list]
        assert any('batch' in str(call).lower() or 'human' in str(call).lower()
                   for call in log_calls), "Expected log message about batch translator"

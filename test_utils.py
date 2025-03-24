import os
import unittest
from unittest.mock import patch, MagicMock
from utils import upload_file, transcribe_audio, check_transcription_status
from dotenv import load_dotenv

load_dotenv()

class TestTranscriptionUtils(unittest.TestCase):
    """Test cases for transcription utility functions."""
    
    def setUp(self):
        """Set up test environment."""
        # Ensure API key is loaded
        self.api_key = os.getenv("ASSEMBLYAI_API_KEY")
        
        # Mock audio file path
        self.test_audio_path = "test_audio.mp3"
        
        # Mock audio URL returned by upload
        self.test_audio_url = "https://api.assemblyai.com/v2/upload/test"
        
        # Mock transcript ID
        self.test_transcript_id = "test_transcript_123"
    
    @patch('assemblyai.Transcriber')
    def test_upload_file(self, mock_transcriber):
        """Test upload_file function."""
        # Mock the transcriber.upload method
        mock_instance = MagicMock()
        mock_transcriber.return_value = mock_instance
        mock_instance.upload.return_value = self.test_audio_url
        
        # Call upload_file and verify result
        result = upload_file(self.test_audio_path)
        
        # Verify transcriber was called correctly
        mock_transcriber.assert_called_once()
        mock_instance.upload.assert_called_once_with(self.test_audio_path)
        
        # Verify result
        self.assertEqual(result, self.test_audio_url)
    
    @patch('assemblyai.Transcriber')
    def test_transcribe_audio_default_config(self, mock_transcriber):
        """Test transcribe_audio function with default config."""
        # Mock the transcriber.transcribe method
        mock_instance = MagicMock()
        mock_transcriber.return_value = mock_instance
        mock_transcript = MagicMock()
        mock_transcript.id = self.test_transcript_id
        mock_instance.transcribe.return_value = mock_transcript
        
        # Call transcribe_audio with default config
        result = transcribe_audio(self.test_audio_url)
        
        # Verify transcriber was called correctly
        mock_transcriber.assert_called_once()
        mock_instance.transcribe.assert_called_once_with(self.test_audio_url)
        
        # Verify result
        self.assertEqual(result.id, self.test_transcript_id)
    
    @patch('assemblyai.Transcriber')
    def test_transcribe_audio_custom_config(self, mock_transcriber):
        """Test transcribe_audio function with custom config."""
        # Mock the transcriber.transcribe method
        mock_instance = MagicMock()
        mock_transcriber.return_value = mock_instance
        mock_transcript = MagicMock()
        mock_transcript.id = self.test_transcript_id
        mock_instance.transcribe.return_value = mock_transcript
        
        # Custom config
        config = {
            'language': 'en',
            'speaker_diarization': True,
            'auto_chapters': True,
            'entity_detection': True,
            'content_moderation': True,
            'format_text': True
        }
        
        # Call transcribe_audio with custom config
        result = transcribe_audio(self.test_audio_url, config)
        
        # Verify transcriber was called correctly
        mock_transcriber.assert_called_once()
        mock_instance.transcribe.assert_called_once_with(
            self.test_audio_url,
            language_code='en',
            speaker_labels=True,
            auto_chapters=True,
            entity_detection=True,
            content_safety=True,
            punctuate=True,
            format_text=True
        )
        
        # Verify result
        self.assertEqual(result.id, self.test_transcript_id)
    
    @patch('assemblyai.Transcriber')
    def test_check_transcription_status(self, mock_transcriber):
        """Test check_transcription_status function."""
        # Mock the transcriber.get_transcript method
        mock_instance = MagicMock()
        mock_transcriber.return_value = mock_instance
        mock_transcript = MagicMock()
        mock_transcript.status = "completed"
        mock_instance.get_transcript.return_value = mock_transcript
        
        # Call check_transcription_status
        result = check_transcription_status(self.test_transcript_id)
        
        # Verify transcriber was called correctly
        mock_transcriber.assert_called_once()
        mock_instance.get_transcript.assert_called_once_with(self.test_transcript_id)
        
        # Verify result
        self.assertEqual(result, "completed")

if __name__ == "__main__":
    unittest.main() 
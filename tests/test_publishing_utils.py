import os
import pytest
from unittest.mock import patch, MagicMock
from providers.publishing.utils import (
    parse_episode_number,
    clean_title_for_part,
    get_video_duration,
    split_video_to_chunks
)

def test_parse_episode_number():
    assert parse_episode_number("Episode 1 - Introduction") == 1
    assert parse_episode_number("Episode 7: The Final Resolution") == 7
    assert parse_episode_number("Ep 4 - Midpoint") == 4
    assert parse_episode_number("E12 - Outro") == 12
    assert parse_episode_number("No Episode Number Title") == 1

def test_clean_title_for_part():
    assert clean_title_for_part("Episode 1 - Introduction") == "Introduction"
    assert clean_title_for_part("Episode 7: The Final Resolution") == "The Final Resolution"
    assert clean_title_for_part("Ep 4 - Midpoint") == "Midpoint"
    assert clean_title_for_part("E12 - Outro") == "Outro"
    assert clean_title_for_part("Plain Title") == "Plain Title"

@patch("subprocess.check_output")
def test_get_video_duration(mock_cmd):
    mock_cmd.return_value = "120.45\n"
    assert get_video_duration("dummy.mp4") == 120.45

@patch("subprocess.run")
@patch("providers.publishing.utils.get_video_duration")
def test_split_video_to_chunks(mock_duration, mock_run):
    mock_duration.return_value = 120.0
    mock_run.return_value = MagicMock(returncode=0)
    
    with patch("tempfile.NamedTemporaryFile") as mock_temp:
        # Mock NamedTemporaryFile to return deterministic names
        mock_file1 = MagicMock()
        mock_file1.name = "temp_chunk_1.mp4"
        mock_file2 = MagicMock()
        mock_file2.name = "temp_chunk_2.mp4"
        mock_file3 = MagicMock()
        mock_file3.name = "temp_chunk_3.mp4"
        
        mock_temp.side_effect = [mock_file1, mock_file2, mock_file3]
        
        # Test split with 55s chunk duration
        chunks = split_video_to_chunks("input.mp4", chunk_duration_sec=55.0)
        
        assert len(chunks) == 3
        assert chunks[0] == "temp_chunk_1.mp4"
        assert chunks[1] == "temp_chunk_2.mp4"
        assert chunks[2] == "temp_chunk_3.mp4"
        
        # Ensure it ran ffmpeg exactly 3 times
        assert mock_run.call_count == 3

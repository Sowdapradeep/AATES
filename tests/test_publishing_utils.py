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

def test_youtube_video_rate_limit(client):
    import datetime
    # 1. Create a youtube_video job for today
    today_iso = datetime.datetime.now(datetime.UTC).date().isoformat() + "T10:00:00"
    
    payload1 = {
        "content_id": "ep-test-rl-1",
        "provider": "youtube_video",
        "priority": 0,
        "scheduled_at": today_iso,
        "payload": {"master_reel_path": "fake.mp4"}
    }
    res1 = client.post("/v1/publishing/jobs", json=payload1)
    assert res1.status_code == 200
    job1_scheduled_at = res1.json()["scheduled_at"]
    
    # 2. Create another youtube_video job for the same day
    payload2 = {
        "content_id": "ep-test-rl-2",
        "provider": "youtube_video",
        "priority": 0,
        "scheduled_at": today_iso,
        "payload": {"master_reel_path": "fake2.mp4"}
    }
    res2 = client.post("/v1/publishing/jobs", json=payload2)
    assert res2.status_code == 200
    job2_scheduled_at = res2.json()["scheduled_at"]
    
    # Assert that job2 was rescheduled to the next day!
    dt1 = datetime.datetime.fromisoformat(job1_scheduled_at.replace("Z", "+00:00"))
    dt2 = datetime.datetime.fromisoformat(job2_scheduled_at.replace("Z", "+00:00"))
    assert dt2.date() == dt1.date() + datetime.timedelta(days=1)

def test_segment_schedule_alignment(client):
    import datetime
    # 1. Create a youtube_video job
    today_iso = datetime.datetime.now(datetime.UTC).date().isoformat() + "T12:00:00"
    payload_main = {
        "content_id": "ep-test-alignment-5",
        "provider": "youtube_video",
        "priority": 0,
        "scheduled_at": today_iso,
        "payload": {"master_reel_path": "fake.mp4"}
    }
    res_main = client.post("/v1/publishing/jobs", json=payload_main)
    assert res_main.status_code == 200
    main_scheduled_at = res_main.json()["scheduled_at"]
    
    # 2. Create a youtube_short segment for the same content_id
    payload_short = {
        "content_id": "ep-test-alignment-5",
        "provider": "youtube_short",
        "priority": 0,
        "scheduled_at": None,
        "payload": {"master_reel_path": "fake_short.mp4"}
    }
    res_short = client.post("/v1/publishing/jobs", json=payload_short)
    assert res_short.status_code == 200
    short_scheduled_at = res_short.json()["scheduled_at"]
    
    dt_main = datetime.datetime.fromisoformat(main_scheduled_at.replace("Z", "+00:00"))
    dt_short = datetime.datetime.fromisoformat(short_scheduled_at.replace("Z", "+00:00"))
    assert dt_short == dt_main + datetime.timedelta(hours=1)


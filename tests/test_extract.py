import pytest
import os
import pandas as pd
from unittest.mock import patch, MagicMock
from etl.extract import (
    extract_csv,
    _fetch_steamspy_bulk,
    _fetch_store_details,
    extract_api,
    _request_with_retry
)
from etl.config import CSV_PATH

def test_extract_csv_fallback():
    assert os.path.exists(CSV_PATH), f"Raw CSV must exist at {CSV_PATH}"
    df = extract_csv(CSV_PATH)
    assert isinstance(df, pd.DataFrame)
    assert len(df) > 0
    assert "appid" in df.columns
    assert "owners" in df.columns
    assert "price" in df.columns

@patch("etl.extract.requests.get")
def test_fetch_steamspy_bulk_mock(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "10": {
            "appid": 10,
            "name": "Counter-Strike",
            "owners": "10000000-20000000",
            "price": "719"
        }
    }
    mock_get.return_value = mock_response

    # Force bypass cache by testing _request_with_retry
    data = _request_with_retry("https://steamspy.com/api.php", params={"request": "all", "page": "0"})
    assert "10" in data
    assert data["10"]["name"] == "Counter-Strike"

@patch("etl.extract.requests.get")
def test_request_with_retry_failure(mock_get):
    import requests
    mock_get.side_effect = requests.RequestException("Network timeout")
    data = _request_with_retry("https://fake-url.com", max_retries=2, backoff=0.01)
    assert data is None

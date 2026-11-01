import pytest
from pydantic import ValidationError
from etl.validate import Game, validate_dataframe
import pandas as pd

def test_game_model_valid():
    valid_data = {
        "appid": 10,
        "name": "Counter-Strike",
        "release_date": "2000-11-01",
        "english": 1,
        "developer": "Valve",
        "publisher": "Valve",
        "platforms": "windows;mac;linux",
        "required_age": 0,
        "categories": "Multi-player;Online Multi-Player",
        "genres": "Action",
        "steamspy_tags": "Action;FPS;Multiplayer",
        "achievements": 0,
        "positive_ratings": 124534,
        "negative_ratings": 3393,
        "average_playtime": 17612,
        "median_playtime": 317,
        "owners": "10000000-20000000",
        "price": 7.19,
        "owners_min": 10000000,
        "owners_max": 20000000,
        "owners_mid": 15000000.0,
        "popularity_tier": "High",
        "release_year": 2000,
        "release_month": 11,
        "is_windows": 1,
        "is_mac": 1,
        "is_linux": 1,
        "is_free": 0,
        "has_multiplayer": 1,
        "has_singleplayer": 0,
        "review_score": 0.973,
    }
    game = Game(**valid_data)
    assert game.appid == 10
    assert game.name == "Counter-Strike"
    assert game.price == 7.19
    assert game.popularity_tier == "High"

def test_game_negative_price_rejected():
    with pytest.raises(ValidationError) as exc:
        Game(
            appid=10,
            name="Negative Price Game",
            release_date="2020-01-01",
            price=-5.0,
            owners="0-20000",
            owners_min=0,
            owners_max=20000,
            popularity_tier="Low"
        )
    assert "price" in str(exc.value)

def test_game_empty_name_rejected():
    with pytest.raises(ValidationError) as exc:
        Game(
            appid=10,
            name="   ",
            release_date="2020-01-01",
            price=9.99,
            owners="0-20000",
            owners_min=0,
            owners_max=20000,
            popularity_tier="Low"
        )
    assert "name" in str(exc.value)

def test_game_negative_achievements_rejected():
    with pytest.raises(ValidationError) as exc:
        Game(
            appid=10,
            name="Negative Achievements",
            release_date="2020-01-01",
            price=9.99,
            achievements=-1,
            owners="0-20000",
            owners_min=0,
            owners_max=20000,
            popularity_tier="Low"
        )
    assert "achievements" in str(exc.value)

def test_game_invalid_tier_rejected():
    with pytest.raises(ValidationError) as exc:
        Game(
            appid=10,
            name="Invalid Tier",
            release_date="2020-01-01",
            price=9.99,
            owners="0-20000",
            owners_min=0,
            owners_max=20000,
            popularity_tier="SuperPopular"
        )
    assert "popularity_tier" in str(exc.value)

def test_validate_dataframe_separation():
    sample_df = pd.DataFrame([
        {
            "appid": 1,
            "name": "Good Game",
            "release_date": "2020-01-01",
            "english": 1,
            "developer": "Dev",
            "publisher": "Pub",
            "platforms": "windows",
            "required_age": 0,
            "categories": "Single-player",
            "genres": "Action",
            "steamspy_tags": "Action",
            "achievements": 5,
            "positive_ratings": 100,
            "negative_ratings": 10,
            "average_playtime": 50,
            "median_playtime": 40,
            "owners": "0-20000",
            "price": 4.99,
            "owners_min": 0,
            "owners_max": 20000,
            "owners_mid": 10000.0,
            "popularity_tier": "Low",
            "release_year": 2020,
            "release_month": 1,
            "is_windows": 1,
            "is_mac": 0,
            "is_linux": 0,
            "is_free": 0,
            "has_multiplayer": 0,
            "has_singleplayer": 1,
            "review_score": 0.909,
        },
        {
            "appid": 2,
            "name": "",  # Invalid: empty name
            "release_date": "2020-01-01",
            "english": 1,
            "developer": "Dev",
            "publisher": "Pub",
            "platforms": "windows",
            "required_age": 0,
            "categories": "Single-player",
            "genres": "Action",
            "steamspy_tags": "Action",
            "achievements": 5,
            "positive_ratings": 100,
            "negative_ratings": 10,
            "average_playtime": 50,
            "median_playtime": 40,
            "owners": "0-20000",
            "price": 4.99,
            "owners_min": 0,
            "owners_max": 20000,
            "owners_mid": 10000.0,
            "popularity_tier": "Low",
            "release_year": 2020,
            "release_month": 1,
            "is_windows": 1,
            "is_mac": 0,
            "is_linux": 0,
            "is_free": 0,
            "has_multiplayer": 0,
            "has_singleplayer": 1,
            "review_score": 0.909,
        },
        {
            "appid": 3,
            "name": "Bad Price Game",
            "release_date": "2020-01-01",
            "english": 1,
            "developer": "Dev",
            "publisher": "Pub",
            "platforms": "windows",
            "required_age": 0,
            "categories": "Single-player",
            "genres": "Action",
            "steamspy_tags": "Action",
            "achievements": 5,
            "positive_ratings": 100,
            "negative_ratings": 10,
            "average_playtime": 50,
            "median_playtime": 40,
            "owners": "0-20000",
            "price": -10.0,  # Invalid: negative price
            "owners_min": 0,
            "owners_max": 20000,
            "owners_mid": 10000.0,
            "popularity_tier": "Low",
            "release_year": 2020,
            "release_month": 1,
            "is_windows": 1,
            "is_mac": 0,
            "is_linux": 0,
            "is_free": 0,
            "has_multiplayer": 0,
            "has_singleplayer": 1,
            "review_score": 0.909,
        }
    ])

    valid_records, rejected_records = validate_dataframe(sample_df)
    assert len(valid_records) == 1
    assert valid_records[0]["appid"] == 1
    assert len(rejected_records) == 2
    assert rejected_records[0]["appid"] == 2
    assert "name" in rejected_records[0]["rejection_reason"]
    assert rejected_records[1]["appid"] == 3
    assert "price" in rejected_records[1]["rejection_reason"]

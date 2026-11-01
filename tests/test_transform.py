import pytest
from etl.transform import parse_owners, assign_tier

def test_parse_owners_standard_range():
    min_val, max_val, mid_val = parse_owners("20000-50000")
    assert min_val == 20000
    assert max_val == 50000
    assert mid_val == 35000.0

def test_parse_owners_zero_low_range():
    min_val, max_val, mid_val = parse_owners("0-20000")
    assert min_val == 0
    assert max_val == 20000
    assert mid_val == 10000.0

def test_parse_owners_large_numbers_with_commas():
    min_val, max_val, mid_val = parse_owners("1,000,000-2,000,000")
    assert min_val == 1000000
    assert max_val == 2000000
    assert mid_val == 1500000.0

def test_parse_owners_invalid_returns_zeros():
    assert parse_owners(None) == (0, 0, 0.0)
    assert parse_owners("invalid_text") == (0, 0, 0.0)

def test_tier_assignment_boundaries():
    # Low: owners_max <= 20,000
    assert assign_tier(0) == "Low"
    assert assign_tier(20000) == "Low"

    # Medium: 20,000 < owners_max <= 200,000
    assert assign_tier(20001) == "Medium"
    assert assign_tier(50000) == "Medium"
    assert assign_tier(200000) == "Medium"

    # High: owners_max > 200,000
    assert assign_tier(200001) == "High"
    assert assign_tier(1000000) == "High"

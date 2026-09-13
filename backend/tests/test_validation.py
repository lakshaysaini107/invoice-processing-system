from backend.utils.date_utils import parse_date
from backend.utils.gst_utils import normalize_gstin, validate_gstin
from backend.utils.math_utils import parse_amount


def test_gstin_validation():
    valid_gst = "29ABCDE1234F1ZH"
    assert validate_gstin(valid_gst) is True
    assert validate_gstin("INVALID_GST") is False
    assert normalize_gstin("29abcde1234f1zh") == valid_gst


def test_date_parsing():
    assert parse_date("2026-09-15") == "2026-09-15"
    assert parse_date("15/09/2026") == "2026-09-15"
    assert parse_date("15-09-2026") == "2026-09-15"


def test_amount_parsing():
    assert parse_amount("₹ 1,234.50") == 1234.50
    assert parse_amount("Rs 500") == 500.0
    assert parse_amount(None) is None

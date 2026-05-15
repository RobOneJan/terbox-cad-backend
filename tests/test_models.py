import pytest
from pydantic import ValidationError
from models import TerBoxConfiguration, QuoteRequestPayload


def test_valid_config(valid_config):
    cfg = TerBoxConfiguration(**valid_config)
    assert cfg.useCase == "urban"


def test_invalid_ral_color(valid_config):
    valid_config["color"] = "blue"
    with pytest.raises(ValidationError, match="RAL"):
        TerBoxConfiguration(**valid_config)


def test_color_other_requires_custom_color(valid_config):
    valid_config["color"] = "other"
    with pytest.raises(ValidationError, match="customColor"):
        TerBoxConfiguration(**valid_config)


def test_color_other_with_custom_color(valid_config):
    valid_config["color"] = "other"
    valid_config["customColor"] = "#1A2B3C"
    cfg = TerBoxConfiguration(**valid_config)
    assert cfg.customColor == "#1A2B3C"


def test_gastronomy_blocks_closure_type(valid_config):
    valid_config["useCase"] = "gastronomy"
    valid_config["closureType"] = "rollerDoor"
    with pytest.raises(ValidationError, match="gastronomy"):
        TerBoxConfiguration(**valid_config)


def test_gastronomy_without_closure_is_valid(valid_config):
    valid_config["useCase"] = "gastronomy"
    valid_config["closureType"] = None
    valid_config["shutterColor"] = None
    cfg = TerBoxConfiguration(**valid_config)
    assert cfg.useCase == "gastronomy"


def test_shutter_color_other_requires_custom(valid_config):
    valid_config["shutterColor"] = "other"
    with pytest.raises(ValidationError, match="customShutterColor"):
        TerBoxConfiguration(**valid_config)


def test_invalid_shutter_color(valid_config):
    valid_config["shutterColor"] = "hotpink"
    with pytest.raises(ValidationError, match="shutterColor"):
        TerBoxConfiguration(**valid_config)


def test_quote_invalid_email(valid_quote):
    valid_quote["email"] = "not-an-email"
    with pytest.raises(ValidationError, match="email"):
        QuoteRequestPayload(**valid_quote)


def test_quote_name_too_long(valid_quote):
    valid_quote["firstName"] = "A" * 101
    with pytest.raises(ValidationError):
        QuoteRequestPayload(**valid_quote)


def test_quote_valid(valid_quote):
    payload = QuoteRequestPayload(**valid_quote)
    assert payload.email == "max@example.com"

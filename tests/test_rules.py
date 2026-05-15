from models import TerBoxConfiguration
from rules import compute_config


def _config(size="medium", custom_length=None) -> TerBoxConfiguration:
    cfg = {
        "useCase": "urban",
        "size": size,
        "mounting": "noMounting",
        "color": "ral7016",
        "floor": "withoutFloor",
        "wallHeight": "none",
        "closureType": "open",
        "features": [],
    }
    if custom_length is not None:
        cfg["customSize"] = {"width": "100", "height": "220", "length": str(custom_length)}
    return TerBoxConfiguration(**cfg)


def test_small_size():
    result = compute_config(_config("small"))
    assert result.module_count == 1
    assert result.module_length_cm == 125.0


def test_medium_size():
    result = compute_config(_config("medium"))
    assert result.module_count == 2
    assert result.module_length_cm == 125.0


def test_large_size():
    result = compute_config(_config("large"))
    assert result.module_count == 3
    assert result.module_length_cm == 125.0


def test_custom_length_exact_multiple():
    # 250 cm → 2 modules of 125 cm each
    result = compute_config(_config(custom_length=250))
    assert result.module_count == 2
    assert result.module_length_cm == 125.0


def test_custom_length_rounds_up():
    # 300 cm → ceil(300/125) = 3 modules of 100 cm each
    result = compute_config(_config(custom_length=300))
    assert result.module_count == 3
    assert result.module_length_cm == 100.0


def test_custom_length_single_module():
    result = compute_config(_config(custom_length=80))
    assert result.module_count == 1
    assert result.module_length_cm == 80.0


def test_custom_length_invalid_falls_back_to_size():
    # Non-numeric length should fall back to size-based count
    result = compute_config(_config("medium", custom_length="abc"))
    assert result.module_count == 2

import pytest
from fastapi.testclient import TestClient
from main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def valid_config():
    """Minimal valid TerBoxConfiguration payload."""
    return {
        "useCase": "urban",
        "size": "medium",
        "mounting": "noMounting",
        "color": "ral7016",
        "floor": "withFloor",
        "floorMaterial": "wpcFloor",
        "floorWpcColor": "darkGrey",
        "wallHeight": "full",
        "wallMaterial": "wpc",
        "wpcColor": "darkGrey",
        "closureType": "rollerDoor",
        "shutterColor": "ral9005",
        "features": ["led", "power"],
    }


@pytest.fixture
def valid_quote(valid_config):
    """Minimal valid QuoteRequestPayload."""
    return {
        "firstName": "Max",
        "lastName": "Muster",
        "email": "max@example.com",
        "subscribeNewsletter": False,
        "configuration": valid_config,
    }

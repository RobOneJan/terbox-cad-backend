def test_compute_config_returns_module_data(client, valid_config):
    res = client.post("/compute-config", json=valid_config)
    assert res.status_code == 200
    data = res.json()
    assert data["module_count"] == 2
    assert data["module_length_cm"] == 125.0


def test_compute_config_invalid_payload(client):
    res = client.post("/compute-config", json={"useCase": "urban"})
    assert res.status_code == 422


def test_compute_config_invalid_color(client, valid_config):
    valid_config["color"] = "notacolor"
    res = client.post("/compute-config", json=valid_config)
    assert res.status_code == 422


def test_generate_cad_returns_step_file(client, valid_config):
    res = client.post("/generate-cad", json=valid_config)
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/octet-stream"
    assert res.headers["content-disposition"].endswith('.step"')


def test_generate_cad_invalid_payload(client):
    res = client.post("/generate-cad", json={})
    assert res.status_code == 422


def test_submit_quote_success(client, valid_quote):
    res = client.post("/api/quotes", json=valid_quote)
    assert res.status_code == 201
    assert res.json()["status"] == "received"


def test_submit_quote_invalid_email(client, valid_quote):
    valid_quote["email"] = "bad-email"
    res = client.post("/api/quotes", json=valid_quote)
    assert res.status_code == 422


def test_submit_quote_missing_required_field(client, valid_quote):
    del valid_quote["firstName"]
    res = client.post("/api/quotes", json=valid_quote)
    assert res.status_code == 422

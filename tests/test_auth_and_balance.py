from __future__ import annotations

from fastapi.testclient import TestClient


def test_register_login_me_and_invalid_login(client: TestClient) -> None:
    register_response = client.post(
        "/auth/register",
        json={"login": "bob", "password": "secret123"},
    )
    assert register_response.status_code == 201
    assert register_response.json()["login"] == "bob"

    login_response = client.post(
        "/auth/login",
        json={"login": "bob", "password": "secret123"},
    )
    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    me_response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["login"] == "bob"

    invalid_login_response = client.post(
        "/auth/login",
        json={"login": "bob", "password": "wrong-password"},
    )
    assert invalid_login_response.status_code == 401


def test_balance_top_up_and_transactions(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    initial_response = client.get("/balance/", headers=auth_headers)
    assert initial_response.status_code == 200
    assert initial_response.json()["credits"] == 0

    top_up_response = client.post(
        "/balance/top-up",
        headers=auth_headers,
        json={"amount": 25, "description": "test top up"},
    )
    assert top_up_response.status_code == 200
    assert top_up_response.json()["credits"] == 25

    balance_response = client.get("/balance/", headers=auth_headers)
    assert balance_response.status_code == 200
    assert balance_response.json()["credits"] == 25

    transactions_response = client.get(
        "/balance/transactions",
        headers=auth_headers,
    )
    assert transactions_response.status_code == 200

    transactions = transactions_response.json()
    assert len(transactions) == 1
    assert transactions[0]["transaction_type"] == "top_up"
    assert transactions[0]["amount"] == 25
    assert transactions[0]["description"] == "test top up"


def test_negative_top_up_is_rejected(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/balance/top-up",
        headers=auth_headers,
        json={"amount": -10},
    )

    assert response.status_code == 422
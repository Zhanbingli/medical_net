from __future__ import annotations


def test_list_drugs_returns_seed_data(client):
    response = client.get("/api/v1/drugs/")
    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert any(item["id"] == "drug_001" for item in payload)


def test_search_filter_matches_expected_drug(client):
    response = client.get("/api/v1/drugs/", params={"q": "B01AC04"})
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == "drug_002"


def test_graph_endpoint_returns_nodes_and_links(client):
    response = client.get("/api/v1/drugs/drug_001/graph")
    assert response.status_code == 200
    graph = response.json()
    assert any(node["type"] == "drug" for node in graph["nodes"])
    assert len(graph["links"]) > 0

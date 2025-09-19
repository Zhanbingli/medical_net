from unittest.mock import patch

import pandas as pd

from pipelines.sources.openfda import OpenFdaAdapter


SAMPLE_RESPONSE = {
    "results": [
        {
            "openfda": {
                "product_ndc": ["0002-8215"],
                "brand_name": ["Aspirin"],
                "substance_name": ["ASPIRIN"],
            },
            "indications_and_usage": ["用于缓解轻度疼痛"],
            "purpose": ["Pain reliever"],
        },
        {
            "openfda": {
                "product_ndc": ["0002-8217"],
                "brand_name": ["Combo Aspirin"],
                "substance_name": ["ACETAMINOPHEN", "ASPIRIN"],
            },
            "indications_and_usage": ["用于缓解轻度疼痛"],
            "purpose": ["Pain reliever"],
        },
        {
            "openfda": {
                "product_ndc": ["0002-8216"],
                "brand_name": ["Clopidogrel"],
                "substance_name": ["CLOPIDOGREL"],
            },
            "indications_and_usage": ["用于减少血栓事件"],
            "purpose": ["Antiplatelet"],
        },
    ]
}


@patch("pipelines.sources.openfda.requests.get")
def test_transform_builds_frames(mock_get):
    mock_get.return_value.json.return_value = SAMPLE_RESPONSE
    mock_get.return_value.raise_for_status.return_value = None
    mock_get.return_value.status_code = 200

    adapter = OpenFdaAdapter({"substances": ["ASPIRIN", "CLOPIDOGREL"]})
    frames = adapter.run()

    drugs = frames["drugs"]
    conditions = frames["conditions"]
    drug_conditions = frames["drug_conditions"]

    assert len(drugs) == 2
    assert set(drugs["id"]) == {"0002-8215", "0002-8216"}
    assert set(drugs["atc_code"]) == {"ASPIRIN", "CLOPIDOGREL"}

    assert len(conditions) == 2
    assert conditions.iloc[0]["name"].startswith("用于")

    assert len(drug_conditions) == 2
    assert all(drug_conditions["drug_id"].isin(drugs["id"]))


@patch("pipelines.sources.openfda.requests.get")
def test_extract_handles_no_match_response(mock_get):
    mock_get.return_value.status_code = 404
    mock_get.return_value.json.return_value = {
        "error": {"code": "NOT_FOUND", "message": "No matches found!"}
    }

    adapter = OpenFdaAdapter({})
    frames = adapter.run()

    assert frames["drugs"].empty
    assert list(frames["drugs"].columns) == ["id", "name", "description", "atc_code"]
    assert frames["conditions"].empty
    assert list(frames["conditions"].columns) == ["id", "name", "description"]
    assert frames["drug_conditions"].empty
    assert list(frames["drug_conditions"].columns) == ["id", "drug_id", "condition_id", "usage_note", "evidence_level"]


@patch("pipelines.sources.openfda.requests.get")
def test_build_params_from_substances(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"results": []}
    mock_get.return_value.raise_for_status.return_value = None

    adapter = OpenFdaAdapter({"substances": ["Aspirin", " Clopidogrel "], "limit": 25})
    list(adapter.extract())

    args, kwargs = mock_get.call_args
    params = kwargs["params"]
    assert params["limit"] == 25
    assert params["search"] == 'openfda.substance_name:"Aspirin" OR openfda.substance_name:"Clopidogrel"'


@patch("pipelines.sources.openfda.requests.get")
def test_filter_rows_skips_non_target_substances(mock_get):
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {
        "results": [
            {
                "openfda": {
                    "product_ndc": ["1111-2222"],
                    "brand_name": ["Other"],
                    "substance_name": ["ACETAMINOPHEN"],
                },
                "purpose": ["Pain"],
            }
        ]
    }
    mock_get.return_value.raise_for_status.return_value = None

    adapter = OpenFdaAdapter({"substances": ["ASPIRIN"]})
    frames = adapter.run()

    assert frames["drugs"].empty

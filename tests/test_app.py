import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static():
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_data():
    response = client.get("/activities")

    assert response.status_code == 200
    data = response.json()
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]
    assert isinstance(data["Chess Club"]["participants"], list)


def test_signup_adds_participant():
    email = "newstudent@mergington.edu"
    response = client.post(
        f"/activities/{quote('Chess Club')}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {email} for Chess Club"

    activities_response = client.get("/activities")
    participants = activities_response.json()["Chess Club"]["participants"]
    assert email in participants


def test_signup_duplicate_returns_400():
    email = "newstudent@mergington.edu"
    client.post(
        f"/activities/{quote('Chess Club')}/signup", params={"email": email}
    )
    response = client.post(
        f"/activities/{quote('Chess Club')}/signup", params={"email": email}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_remove_participant_success():
    email = "michael@mergington.edu"
    response = client.delete(
        f"/activities/{quote('Chess Club')}/participants", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from Chess Club"

    activities_response = client.get("/activities")
    participants = activities_response.json()["Chess Club"]["participants"]
    assert email not in participants


def test_remove_participant_missing_returns_404():
    response = client.delete(
        f"/activities/{quote('Chess Club')}/participants", params={"email": "missing@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_signup_invalid_activity_returns_404():
    response = client.post(
        f"/activities/{quote('Unknown Club')}/signup", params={"email": "new@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_invalid_activity_returns_404():
    response = client.delete(
        f"/activities/{quote('Unknown Club')}/participants", params={"email": "new@mergington.edu"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"

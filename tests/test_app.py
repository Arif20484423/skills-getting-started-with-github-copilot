from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def activities(monkeypatch):
    activity_data = {
        "Chess Club": {
            "description": "Learn chess",
            "schedule": "Fridays",
            "max_participants": 3,
            "participants": ["existing@example.com"],
        },
        "Art Club": {
            "description": "Make art",
            "schedule": "Mondays",
            "max_participants": 2,
            "participants": [],
        },
    }
    monkeypatch.setattr(app_module, "activities", activity_data)
    return activity_data


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_root_redirects_to_frontend(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_data(client, activities):
    # Arrange
    expected_activities = activities

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_participant(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "new@example.com"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert activities[activity_name]["participants"] == ["existing@example.com", email]


def test_signup_rejects_duplicate_participant(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "existing@example.com"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.post(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up for this activity"}
    assert activities[activity_name]["participants"] == original_participants


def test_signup_rejects_unknown_activity(client, activities):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.post(signup_path, params={"email": "new@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert "Unknown Club" not in activities


def test_remove_participant_removes_signup(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "existing@example.com"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert activities[activity_name]["participants"] == []


def test_remove_participant_rejects_unknown_activity(client, activities):
    # Arrange
    activity_name = "Unknown Club"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"

    # Act
    response = client.delete(signup_path, params={"email": "new@example.com"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert "Unknown Club" not in activities


def test_remove_participant_rejects_unregistered_email(client, activities):
    # Arrange
    activity_name = "Chess Club"
    email = "missing@example.com"
    signup_path = f"/activities/{quote(activity_name, safe='')}/signup"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.delete(signup_path, params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up for this activity"}
    assert activities[activity_name]["participants"] == original_participants
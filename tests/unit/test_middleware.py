from fastapi import FastAPI
from fastapi.testclient import TestClient

from fluxcrud.core.exceptions import (
    ConfigurationError,
    DatabaseError,
    NotFoundError,
    ValidationError,
)
from fluxcrud.web.middleware import ValidationMiddleware

app = FastAPI()
app.add_middleware(ValidationMiddleware)


@app.get("/not-found")
def raise_not_found():
    raise NotFoundError("Record not found")


@app.get("/validation-error")
def raise_validation_error():
    raise ValidationError("Invalid data")


@app.get("/config-error")
def raise_config_error():
    raise ConfigurationError("Bad config")


@app.get("/db-error")
def raise_db_error():
    raise DatabaseError("DB connection failed")


@app.get("/generic-error")
def raise_generic_error():
    raise Exception("Something went wrong")


client = TestClient(app)


def test_not_found_error():
    response = client.get("/not-found")
    assert response.status_code == 404
    assert response.json() == {"detail": "Record not found"}


def test_validation_error():
    response = client.get("/validation-error")
    assert response.status_code == 422
    assert response.json() == {"detail": "Invalid data"}


def test_config_error():
    response = client.get("/config-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Bad config"}


def test_db_error():
    response = client.get("/db-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "DB connection failed"}


def test_generic_error():
    response = client.get("/generic-error")
    assert response.status_code == 500
    assert response.json() == {"detail": "Something went wrong"}

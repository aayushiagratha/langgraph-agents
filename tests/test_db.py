from unittest.mock import patch

import pytest

import common.db as db


def test_get_connection_passes_env_vars_through(monkeypatch):
    monkeypatch.setenv("PGHOST", "db.example.com")
    monkeypatch.setenv("PGDATABASE", "mydb")
    monkeypatch.setenv("PGUSER", "myuser")
    monkeypatch.setenv("PGPASSWORD", "mypass")
    monkeypatch.delenv("PGPORT", raising=False)

    with patch("common.db.psycopg.connect") as mock_connect:
        db.get_connection()
        mock_connect.assert_called_once_with(
            host="db.example.com",
            port="5432",
            dbname="mydb",
            user="myuser",
            password="mypass",
            sslmode="require",
        )


def test_get_connection_uses_explicit_port(monkeypatch):
    monkeypatch.setenv("PGHOST", "db.example.com")
    monkeypatch.setenv("PGPORT", "6543")
    monkeypatch.setenv("PGDATABASE", "mydb")
    monkeypatch.setenv("PGUSER", "myuser")
    monkeypatch.setenv("PGPASSWORD", "mypass")

    with patch("common.db.psycopg.connect") as mock_connect:
        db.get_connection()
        assert mock_connect.call_args.kwargs["port"] == "6543"


def test_get_connection_requires_host(monkeypatch):
    monkeypatch.delenv("PGHOST", raising=False)
    monkeypatch.setenv("PGDATABASE", "mydb")
    monkeypatch.setenv("PGUSER", "myuser")
    monkeypatch.setenv("PGPASSWORD", "mypass")
    with pytest.raises(KeyError):
        db.get_connection()

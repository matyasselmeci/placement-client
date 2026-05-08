import base64
import json

import pytest

from placement import common


def _make_token(expiration: float) -> bytes:
    body = base64.urlsafe_b64encode(
        json.dumps({"exp": expiration}).encode("utf-8")
    ).rstrip(b"=")
    return b"header." + body + b".signature"


def test_get_token_state_reports_missing(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "get_condor_tokens_dir", lambda create=False: tmp_path)

    assert common.get_token_state("Placement.token") is common.TokenState.MISSING


def test_get_token_state_reports_unreadable(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "get_condor_tokens_dir", lambda create=False: tmp_path)
    (tmp_path / "Placement.token").write_bytes(b"not a jwt")

    assert common.get_token_state("Placement.token") is common.TokenState.UNREADABLE


def test_get_token_state_reports_expired_and_ok(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "get_condor_tokens_dir", lambda create=False: tmp_path)
    monkeypatch.setattr(common.time, "time", lambda: 1000.0)

    token_path = tmp_path / "Placement.token"
    token_path.write_bytes(_make_token(900.0))
    assert common.get_token_state("Placement.token") is common.TokenState.EXPIRED

    token_path.write_bytes(_make_token(1100.0))
    assert common.get_token_state("Placement.token") is common.TokenState.OK


def test_write_token_writes_file_with_permissions(monkeypatch, tmp_path):
    monkeypatch.setattr(common, "get_condor_tokens_dir", lambda create=True: tmp_path)

    token_path = common.write_token("Placement.token", b"abc123")

    assert token_path == tmp_path / "Placement.token"
    assert token_path.read_bytes() == b"abc123"
    assert oct(token_path.stat().st_mode & 0o777) == "0o600"


@pytest.mark.parametrize(
    "token_filename",
    ["../Placement.token", r"Placement\\token", "Placement:token"],
)
def test_token_filename_validation_rejects_path_separators(
    monkeypatch, tmp_path, token_filename
):
    monkeypatch.setattr(common, "get_condor_tokens_dir", lambda create=True: tmp_path)

    with pytest.raises(ValueError):
        common.write_token(token_filename, b"abc123")

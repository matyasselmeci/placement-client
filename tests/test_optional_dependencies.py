import pytest

pytest.importorskip("ipywidgets")
pytest.importorskip("IPython")
htcondor2 = pytest.importorskip("htcondor2")

from placement_client import common, jupyter


def test_jupyter_module_imports_when_optional_dependencies_exist():
    assert hasattr(jupyter, "TokenFileUploadWidgets")
    assert hasattr(jupyter, "DeviceWidgets")


def test_get_condor_tokens_dir_uses_htcondor_configuration(monkeypatch, tmp_path):
    monkeypatch.setitem(htcondor2.param, "SEC_TOKEN_DIRECTORY", str(tmp_path))

    assert common.get_condor_tokens_dir(create=False) == tmp_path

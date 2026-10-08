"""Warm the real baseline ELP so downstream assertions can be compared independently of startup."""

import time

import pytest

from solidlsp.ls_config import LanguageServerId
from solidlsp.ls_exceptions import SolidLSPException


@pytest.fixture(autouse=True)
def warm_baseline_elp(request: pytest.FixtureRequest) -> None:
    if "language_server" not in request.fixturenames:
        return
    language_server = request.getfixturevalue("language_server")
    if language_server.ls_id != LanguageServerId.ERLANG:
        return
    with language_server.open_file("hello.erl"):
        for attempt in range(26):
            try:
                language_server.request_document_symbols("hello.erl")
                return
            except SolidLSPException as error:
                if getattr(error.cause, "code", None) != -32801 or attempt == 25:
                    raise
                time.sleep(0.2)

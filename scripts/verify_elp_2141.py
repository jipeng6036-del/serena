"""Real ELP verification, kept only on the fork's verification branch."""

import json
import logging
import sys
import tempfile
import time
from pathlib import Path

from solidlsp import SolidLanguageServer
from solidlsp.ls_config import LanguageServerConfig, LanguageServerId
from solidlsp.ls_exceptions import SolidLSPException
from solidlsp.settings import SolidLSPSettings

logging.basicConfig(level=logging.INFO)
variant = sys.argv[1]
with tempfile.TemporaryDirectory(prefix=f"elp-2141-{variant}-") as directory:
    root = Path(directory)
    (root / "src").mkdir()
    (root / "rebar.config").write_text("{erl_opts, [debug_info]}.\n{deps, []}.\n")
    (root / "src" / "demo.app.src").write_text(
        '{application, demo, [{description, "startup verification"}, {vsn, "0.1.0"}, '
        "{registered, []}, {applications, [kernel, stdlib]}, {env, []}, {modules, []}]}.\n"
    )
    (root / "src" / "demo.erl").write_text("-module(demo).\n-export([greet/0]).\ngreet() -> hello.\n")
    server = SolidLanguageServer.create(
        LanguageServerConfig(LanguageServerId.ERLANG, trace_lsp_communication=True),
        str(root),
        solidlsp_settings=SolidLSPSettings(solidlsp_dir="/tmp/serena-2141-lsp", project_data_path=str(root / ".serena")),
    )
    with server.start():
        started = time.monotonic()
        try:
            result = server.request_document_symbols("src/demo.erl")
        except SolidLSPException as error:
            print(json.dumps({"variant": variant, "first_request": "error", "error": str(error)}))
            if variant == "fixed":
                raise
            time.sleep(0.5)
            result = server.request_document_symbols("src/demo.erl")
        symbols, _roots = result.get_all_symbols_and_roots()
        names = [symbol["name"] for symbol in symbols]
        print(json.dumps({"variant": variant, "symbols": names, "seconds": time.monotonic() - started}))
        assert "greet#0" in names, names

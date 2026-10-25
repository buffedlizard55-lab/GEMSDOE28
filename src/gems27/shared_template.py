"""Load the immutable upstream shared evaluator/writer, never a private code fork.

The upstream source lives in ignored data/shared_template and is verified before
import. Restoring it is an explicit command; imports never use the network.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]
PIN = ROOT / "registry/protocol_assets.json"
PACKAGE = "_gems28_pinned_shared_template"


def verify_assets(root: Path = ROOT, pin: Path | None = None) -> dict:
    pin = pin or root / "registry/protocol_assets.json"
    manifest = json.loads(pin.read_text())
    if (not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list)
            or not isinstance(manifest.get("source"), str)):
        raise ValueError("Malformed shared asset manifest")
    failures, verified, destinations = [], [], set()
    required = {f"shared_template/src/gems/{name}.py" for name in
                ("__init__", "metric", "validator", "holdout", "novelty", "submission")}
    for entry in manifest["files"]:
        if (not isinstance(entry, dict) or not isinstance(entry.get("id"), str)
                or not isinstance(entry.get("dest"), str)
                or not isinstance(entry.get("sha256"), str)
                or not re.fullmatch(r"[0-9a-f]{64}", entry["sha256"])
                or not isinstance(entry.get("bytes"), int) or isinstance(entry["bytes"], bool)
                or entry["bytes"] < 0):
            raise ValueError("Malformed shared asset entry")
        relative = Path(entry["dest"])
        if str(relative) in destinations:
            raise ValueError("Duplicate shared asset destination")
        destinations.add(str(relative))
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Shared asset destination escapes data directory")
        path = root / "data" / relative
        if not path.resolve().is_relative_to((root / "data").resolve()):
            raise ValueError("Shared asset symlink escapes data directory")
        if not path.is_file():
            failures.append(f"missing: {entry['id']}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"] or path.stat().st_size != entry["bytes"]:
            failures.append(f"checksum/size mismatch: {entry['id']}")
        else:
            verified.append({"id": entry["id"], "dest": str(relative), "sha256": digest, "bytes": entry["bytes"]})
    failures.extend(f"unlisted required shared source: {path}" for path in sorted(required - destinations))
    return {"passed": not failures and bool(verified), "files": verified, "failures": failures,
            "manifest_sha256": hashlib.sha256(pin.read_bytes()).hexdigest(),
            "source": manifest["source"], "network_access": "none"}


def load_shared(root: Path = ROOT, pin: Path | None = None) -> ModuleType:
    """Return a hash-verified package with upstream holdout/metric/novelty/submission."""
    check = verify_assets(root, pin)
    if not check["passed"]:
        raise ValueError("Shared template integrity failed: " + "; ".join(check["failures"]))
    init = root / "data/shared_template/src/gems/__init__.py"
    # Derive the namespace from the root as well as pins to avoid sharing imports
    # across checkouts/tests or silently reusing modules from a different source.
    identity = hashlib.sha256((str(root.resolve()) + check["manifest_sha256"]).encode()).hexdigest()[:16]
    name = PACKAGE + "_" + identity
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, init, submodule_search_locations=[str(init.parent)])
    if spec is None or spec.loader is None:
        raise ImportError("Cannot load pinned shared package")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    def execute_verified(target, path):
        data = path.read_bytes()
        destination = str(path.relative_to(root / "data"))
        expected = next(row["sha256"] for row in check["files"] if row["dest"] == destination)
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError("Shared source changed after integrity verification")
        # Execute verified source bytes, never a stale/unverified __pycache__ file.
        exec(compile(data, str(path), "exec"), target.__dict__)

    try:
        execute_verified(module, init)
        for child in ("validator", "metric", "holdout", "novelty", "submission"):
            child_path = init.parent / (child + ".py")
            if not re.fullmatch(r"[a-z_]+", child):
                raise ValueError("Invalid shared module name")
            child_spec = importlib.util.spec_from_file_location(name + "." + child, child_path)
            if child_spec is None or child_spec.loader is None:
                raise ImportError(child)
            child_module = importlib.util.module_from_spec(child_spec)
            sys.modules[child_spec.name] = child_module
            execute_verified(child_module, child_path)
            setattr(module, child, child_module)
    except BaseException:
        for key in list(sys.modules):
            if key == name or key.startswith(name + "."):
                del sys.modules[key]
        raise
    return module

"""Read-only validation for the research-hub catalog (Python 3.10+)."""

import argparse
import json
from pathlib import Path, PurePosixPath, PureWindowsPath


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def validate(root, require_local=()):
    root = Path(root).resolve()
    errors = []
    report = {"ok": False, "sources": 0, "modules": 0,
              "local_entries": 0, "missing_entries": 0, "errors": errors}
    try:
        catalog = json.loads((root / "catalog.json").read_text(encoding="utf-8-sig"),
                             object_pairs_hook=unique_object)
    except (OSError, UnicodeError, ValueError) as exc:
        errors.append(f"Cannot read catalog.json: {exc}")
        return report
    if not isinstance(catalog, dict):
        errors.append("Expected a JSON object")
        return report
    extra = sorted(set(catalog) - {"sources", "modules"})
    if extra:
        errors.append(f"Unsupported catalog fields: {', '.join(extra)}")
    source_records = catalog.get("sources")
    if not isinstance(source_records, list) or not isinstance(catalog.get("modules"), list):
        errors.append("sources and modules must both be arrays")
        return report

    def fields(record, required, label):
        if not isinstance(record, dict):
            errors.append(f"{label}: expected an object")
            return False
        extra = sorted(set(record) - set(required))
        if extra:
            errors.append(f"{label}: unsupported fields: {', '.join(extra)}")
        invalid = [key for key in required
                   if not isinstance(record.get(key), str) or not record[key].strip()]
        if invalid:
            errors.append(f"{label}: expected nonempty strings for: {', '.join(invalid)}")
        return not invalid and not extra

    def relative(value, label):
        windows = PureWindowsPath(value)
        parts = value.split("/")
        if windows.drive or windows.root or "\\" in value or any(p in ("", ".", "..") for p in parts):
            errors.append(f"{label}: expected a relative path with / separators and no . or .. segments")
            return None
        if any(any(char in part for char in '<>:"|?*\0') for part in parts):
            errors.append(f"{label}: invalid path characters")
            return None
        return PurePosixPath(value)

    sources = set()
    source_keys = set()
    for index, source in enumerate(source_records):
        label = f"sources[{index}]"
        if not fields(source, ("id", "repo"), label):
            continue
        source_id = relative(source["id"], f"{label}.id")
        if source_id is None:
            continue
        if len(source_id.parts) != 1:
            errors.append(f"{label}: id must be one directory name")
            continue
        source_key = source["id"].casefold()
        if source_key in source_keys:
            errors.append(f"{label}: duplicate source id {source['id']}")
        source_keys.add(source_key)
        sources.add(source["id"])

    entries = {}
    targets = set()
    for index, module in enumerate(catalog["modules"]):
        label = f"modules[{index}]"
        if not fields(module, ("name", "path", "purpose", "use_when"), label):
            continue
        path = relative(module["path"], f"{label}.path")
        if path is None:
            continue
        if path.name != "SKILL.md":
            errors.append(f"{label}: path must point to SKILL.md")
        if len(path.parts) < 3 or path.parts[0] != "modules":
            errors.append(f"{label}: path must be under modules/<source id>/")
        elif path.parts[1] not in sources:
            errors.append(f"{label}: unknown source directory {path.parts[1]}")
        key = str(path).casefold()
        if key in entries:
            errors.append(f"{label}: duplicate module path {path}")
            continue
        entries[key] = None
        try:
            target = (root / path).resolve()
        except (OSError, RuntimeError, ValueError) as exc:
            errors.append(f"{label}: cannot resolve path: {exc}")
            continue
        if not target.is_relative_to(root):
            errors.append(f"{label}: resolved path escapes hub root")
            continue
        identity = str(target).casefold()
        if identity in targets:
            errors.append(f"{label}: resolved entry path is already registered")
        targets.add(identity)
        entries[key] = target.is_file()
        if not entries[key]:
            errors.append(f"{label}: local entry is missing or is not a file: {path}")

    for selector in require_local:
        path = relative(selector, "--require-local")
        if path is None:
            continue
        key = str(path).casefold()
        if key not in entries:
            errors.append(f"Required path is not registered: {selector}")
        elif entries[key] is not True:
            errors.append(f"Required local entry is missing: {selector}")

    report.update(ok=not errors, sources=len(source_records),
                  modules=len(catalog["modules"]),
                  local_entries=sum(value is True for value in entries.values()),
                  missing_entries=sum(value is False for value in entries.values()))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3],
                        help="Hub directory; defaults to this script's containing hub")
    parser.add_argument("--require-local", action="append", default=[], metavar="PATH",
                        help="Require a module's relative local entry path; may be repeated")
    args = parser.parse_args()
    report = validate(args.root, args.require_local)
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

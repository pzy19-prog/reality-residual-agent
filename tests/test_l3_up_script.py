"""Offline checks that the L3 setup script loads the whitelisted pg columns."""
import ast
import re
from pathlib import Path

from rra.evidence.sources import C1

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "l3_zetaris_up.sh"
PG_TABLES = ("observation_samples", "presence_events", "command_feedback")


def _heredoc(text: str, name: str) -> str:
    match = re.search(rf"<<'{name}'[^\n]*\n(.*?)\n{name}(?:\n|$)", text, re.S)
    if match is None:
        raise AssertionError(f"heredoc {name} not found")
    return match.group(1)


def parse_create_columns(text: str) -> dict[str, list[str]]:
    sql = _heredoc(text, "SQL")
    tables: dict[str, list[str]] = {}
    for match in re.finditer(r"CREATE TABLE\s+(\w+)\s*\((.*?)\)\s*;", sql, re.S):
        columns = []
        for part in match.group(2).split(","):
            name = part.strip().split()[0]
            if name:
                columns.append(name)
        tables[match.group(1)] = columns
    return tables


def parse_copy_columns(text: str) -> dict[str, tuple[str, ...]]:
    module = ast.parse(_heredoc(text, "PY"))
    value = None
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id == "COLUMNS":
                value = node.value
    if not isinstance(value, ast.Dict):
        raise AssertionError("COPY COLUMNS dict not found")
    columns: dict[str, tuple[str, ...]] = {}
    for key, item in zip(value.keys, value.values):
        if not isinstance(key, ast.Constant) or not isinstance(key.value, str):
            raise AssertionError("COPY COLUMNS key is not a string")
        if not isinstance(item, ast.Tuple):
            raise AssertionError(f"COPY fields for {key.value} are not a tuple")
        fields = []
        for element in item.elts:
            if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                raise AssertionError(f"COPY field for {key.value} is not a string")
            fields.append(element.value)
        columns[key.value] = tuple(fields)
    return columns


def test_pg_create_and_copy_columns_match_c1():
    text = SCRIPT.read_text(encoding="utf-8")
    created = parse_create_columns(text)
    copied = parse_copy_columns(text)
    assert set(created) == set(PG_TABLES)
    assert set(copied) == set(PG_TABLES)
    for table in PG_TABLES:
        assert set(created[table]) == C1[table]
        assert set(copied[table]) == C1[table]
        assert tuple(created[table]) == tuple(copied[table])

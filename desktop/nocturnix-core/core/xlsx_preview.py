from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

NS = {
    "main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "rel": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "pkg": "http://schemas.openxmlformats.org/package/2006/relationships",
}


@dataclass(frozen=True)
class SheetPreview:
    name: str
    rows: list[list[str]]


def _column_index(reference: str) -> int:
    letters = re.match(r"[A-Z]+", reference.upper())
    if not letters:
        return 0
    value = 0
    for char in letters.group(0):
        value = value * 26 + ord(char) - 64
    return value - 1


def read_workbook(path: Path, max_rows: int | None = None) -> list[SheetPreview]:
    """Read cached worksheet values without modifying the workbook."""
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for item in root.findall("main:si", NS):
                shared_strings.append("".join(t.text or "" for t in item.findall(".//main:t", NS)))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        targets = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relationships.findall("pkg:Relationship", NS)}
        results: list[SheetPreview] = []

        for sheet in workbook.findall("main:sheets/main:sheet", NS):
            name = sheet.attrib.get("name", "Sheet")
            relationship_id = sheet.attrib.get(f"{{{NS['rel']}}}id")
            target = targets.get(relationship_id or "")
            if not target:
                continue
            worksheet_path = "xl/" + target.lstrip("/")
            root = ET.fromstring(archive.read(worksheet_path))
            rows: list[list[str]] = []
            xml_rows = root.findall("main:sheetData/main:row", NS)
            if max_rows is not None:
                xml_rows = xml_rows[:max_rows]
            for row in xml_rows:
                values: list[str] = []
                for cell in row.findall("main:c", NS):
                    reference = cell.attrib.get("r", "A1")
                    index = _column_index(reference)
                    while len(values) <= index:
                        values.append("")
                    cell_type = cell.attrib.get("t")
                    value_node = cell.find("main:v", NS)
                    inline = cell.find("main:is", NS)
                    value = ""
                    if inline is not None:
                        value = "".join(t.text or "" for t in inline.findall(".//main:t", NS))
                    elif value_node is not None:
                        raw = value_node.text or ""
                        if cell_type == "s" and raw.isdigit():
                            position = int(raw)
                            value = shared_strings[position] if position < len(shared_strings) else raw
                        elif cell_type == "b":
                            value = "TRUE" if raw == "1" else "FALSE"
                        else:
                            value = raw
                    values[index] = value
                rows.append(values)
            results.append(SheetPreview(name=name, rows=rows))
        return results


def read_workbook_preview(path: Path, max_rows: int = 100) -> list[SheetPreview]:
    return read_workbook(path, max_rows=max_rows)

from pathlib import Path
from xml.etree import ElementTree as ET
from zipfile import ZipFile
import re

DOCX = Path("tmp/docs/current_diploma.docx")
OUT = Path("dilpom3")
ASSETS = OUT / "assets"

NS = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}

heading_re = re.compile(r"^([0-9]+)\.([0-9]+)\.\s+(.+)")
chapter_re = re.compile(r"^ГЛАВА\s+([0-9]+)\.\s+(.+)", re.I)


def slugify(text: str) -> str:
    text = text.lower().replace("ё", "е")
    text = re.sub(r"[«»\"“”]", "", text)
    text = re.sub(r"[^0-9a-zа-я._\-]+", "_", text, flags=re.I)
    text = re.sub(r"_+", "_", text).strip("_.")
    return text[:120]


def para_text(p) -> str:
    parts: list[str] = []
    for node in p.iter():
        tag = node.tag.rsplit("}", 1)[-1]
        if tag == "t" and node.text:
            parts.append(node.text)
        elif tag == "tab":
            parts.append("\t")
        elif tag == "br":
            parts.append("\n")
    return "".join(parts).strip()


def table_to_md(tbl) -> list[str]:
    rows: list[list[str]] = []
    for tr in tbl.findall("w:tr", NS):
        cells: list[str] = []
        for tc in tr.findall("w:tc", NS):
            texts: list[str] = []
            for p in tc.findall(".//w:p", NS):
                t = para_text(p)
                if t:
                    texts.append(t.replace("\n", "<br>"))
            cells.append(" ".join(texts).replace("|", "\\|").strip())
        if cells:
            rows.append(cells)
    if not rows:
        return []

    maxcols = max(len(r) for r in rows)
    rows = [r + [""] * (maxcols - len(r)) for r in rows]
    out = [
        "| " + " | ".join(rows[0]) + " |",
        "| " + " | ".join(["---"] * maxcols) + " |",
    ]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out


def start_new_section(title: str):
    m_ch = chapter_re.match(title)
    m_sec = heading_re.match(title)

    if title == "ТЕЗАУРУС":
        return True, "02_тезаурус.md", "# " + title
    if title == "ВВЕДЕНИЕ":
        return True, "03_введение.md", "# " + title
    if title == "ЗАКЛЮЧЕНИЕ":
        return True, "24_заключение.md", "# " + title
    if title == "СПИСОК ЛИТЕРАТУРЫ":
        return True, "25_список_литературы.md", "# " + title

    if m_ch:
        n = int(m_ch.group(1))
        num = {1: 4, 2: 9, 3: 11, 4: 15, 5: 22}.get(n, 99)
        return True, f"{num:02d}_{slugify(title)}.md", "# " + title

    if m_sec:
        major, minor = int(m_sec.group(1)), int(m_sec.group(2))
        if minor == 1:
            return False, None, "## " + title
        mapping = {
            (1, 2): 5,
            (1, 3): 6,
            (1, 4): 7,
            (1, 5): 8,
            (2, 2): 10,
            (3, 2): 12,
            (3, 3): 13,
            (3, 4): 14,
            (4, 2): 16,
            (4, 3): 17,
            (4, 4): 18,
            (4, 5): 19,
            (4, 6): 20,
            (4, 7): 21,
            (5, 2): 23,
        }
        num = mapping.get((major, minor), 90 + major * 10 + minor)
        return True, f"{num:02d}_{slugify(title)}.md", "## " + title

    return False, None, title


def main() -> None:
    with ZipFile(DOCX) as z:
        document_xml = z.read("word/document.xml")
        rels_xml = z.read("word/_rels/document.xml.rels")
        relroot = ET.fromstring(rels_xml)
        rels = {rel.attrib["Id"]: rel.attrib["Target"] for rel in relroot}
        media_data = {
            name: z.read(name)
            for name in z.namelist()
            if name.startswith("word/media/")
        }

    root = ET.fromstring(document_xml)
    body = root.find("w:body", NS)
    image_counter = 0
    image_name_by_rel: dict[str, str] = {}

    OUT.mkdir(exist_ok=True)
    ASSETS.mkdir(exist_ok=True)
    for md in OUT.glob("*.md"):
        md.unlink()
    for old in ASSETS.glob("*"):
        if old.is_file():
            old.unlink()

    sections: list[dict[str, object]] = []
    current: dict[str, object] = {
        "filename": "01_титульные_и_вводные_страницы.md",
        "lines": ["# Титульные и вводные страницы"],
    }
    sections.append(current)

    for child in body:
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            text = para_text(child)
            image_refs: list[str] = []
            for blip in child.findall(".//a:blip", NS):
                rid = blip.attrib.get("{%s}embed" % NS["r"])
                if not rid or rid not in rels:
                    continue
                target = rels[rid]
                media_path = "word/" + target if not target.startswith("word/") else target
                media_path = media_path.replace("word/../", "")
                if media_path not in media_data:
                    continue
                if rid not in image_name_by_rel:
                    image_counter += 1
                    ext = Path(media_path).suffix or ".png"
                    name = f"image_{image_counter:03d}{ext}"
                    image_name_by_rel[rid] = name
                    (ASSETS / name).write_bytes(media_data[media_path])
                image_refs.append(image_name_by_rel[rid])

            if text:
                starts, filename, heading = start_new_section(text)
                if starts:
                    current = {"filename": filename, "lines": [heading]}
                    sections.append(current)
                else:
                    current["lines"].append("")
                    current["lines"].append(heading)

            for img in image_refs:
                current["lines"].append("")
                current["lines"].append(f"![Изображение](assets/{img})")

        elif tag == "tbl":
            md = table_to_md(child)
            if md:
                current["lines"].append("")
                current["lines"].extend(md)

    merged: dict[str, list[str]] = {}
    order: list[str] = []
    for sec in sections:
        fn = str(sec["filename"])
        lines = list(sec["lines"])
        if fn not in merged:
            merged[fn] = lines
            order.append(fn)
        else:
            merged[fn].append("")
            merged[fn].extend(lines)

    for fn in order:
        content = "\n".join(merged[fn]).strip() + "\n"
        (OUT / fn).write_text(content, encoding="utf-8")

    readme = [
        "# Содержимое диплома",
        "",
        "Файлы пересобраны из актуального DOCX по разделам и подглавам.",
        "",
    ]
    for fn in order:
        readme.append(f"- [{fn}]({fn})")
    (OUT / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")

    print(f"created {len(order)} markdown files")
    print(f"extracted {image_counter} images")
    for fn in order:
        print(fn)


if __name__ == "__main__":
    main()

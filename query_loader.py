from pathlib import Path
import re

def load_named_queries(path="queries/complex.sql"):
    txt = Path(path).read_text(encoding="utf-8")
    parts = re.split(r"^--\s*name:\s*(.+)$", txt, flags=re.M)
    names = {}
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        sql = parts[i+1].strip()
        if title and sql:
            names[title] = sql
    return names

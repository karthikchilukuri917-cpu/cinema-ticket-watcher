from pathlib import Path
import re

html = Path("data/hyderabad_cinemas_raw.html").read_text(encoding="utf-8")

patterns = [
    r'.{0,300}ART.{0,500}',
    r'.{0,300}/cinemas/.{0,500}',
]

for pattern in patterns:
    print("\n" + "=" * 100)
    print("PATTERN:", pattern)
    print("=" * 100)

    matches = re.findall(pattern, html, flags=re.IGNORECASE)

    for i, match in enumerate(matches[:10], 1):
        print(f"\n--- MATCH {i} ---")
        print(match)

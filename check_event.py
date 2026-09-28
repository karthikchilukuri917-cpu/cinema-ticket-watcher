import re

path = r"data\debug_pvr_page.html"

html = open(path, encoding="utf-8").read()

print("HTML LENGTH:", len(html))

matches = list(re.finditer(r'"Event"\s*:\s*\[', html))

print("EXACT Event ARRAY COUNT:", len(matches))

if matches:
    print("FIRST POSITION:", matches[0].start())
    print("\n--- CONTEXT ---")
    start = max(0, matches[0].start() - 200)
    end = min(len(html), matches[0].start() + 1000)
    print(html[start:end])

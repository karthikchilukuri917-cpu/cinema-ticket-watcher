import re

path = r"data\debug_pvr_20260924.html"
html = open(path, encoding="utf-8").read()

print("=== DATE REFERENCES ===")

patterns = [
    r"2026092[0-9]",
    r"2026-09-2[0-9]",
]

found = set()

for pattern in patterns:
    for match in re.findall(pattern, html):
        found.add(match)

for value in sorted(found):
    print(value)

print("\n=== POSSIBLE DATE/API REFERENCES ===")

keywords = [
    "showDate",
    "show_date",
    "ShowDate",
    "date",
    "Date",
    "calendar",
    "Calendar",
    "buytickets",
    "showtimes",
    "ShowTimes",
]

for keyword in keywords:
    count = html.count(keyword)
    if count:
        print(f"{keyword}: {count}")

print("\n=== URLS CONTAINING DATE/API INFORMATION ===")

urls = re.findall(r'https?://[^\"\\s]+', html)

for url in urls:
    if any(x in url.lower() for x in ["show", "ticket", "cinema", "date", "calendar"]):
        print(url[:500])

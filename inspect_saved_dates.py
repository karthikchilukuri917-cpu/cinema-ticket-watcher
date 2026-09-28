from app.providers.bookmyshow_html import BookMyShowHTMLParser

path = r"data\debug_pvr_20260924.html"

html = open(path, encoding="utf-8").read()

parser = BookMyShowHTMLParser()
events = parser._extract_event_array(html)

dates = {}

def walk(value):
    if isinstance(value, list):
        for item in value:
            walk(item)

    elif isinstance(value, dict):
        if "ShowDateTime" in value:
            dt = str(value["ShowDateTime"])
            dates[dt[:8]] = dates.get(dt[:8], 0) + 1

        for child in value.values():
            if isinstance(child, (dict, list)):
                walk(child)

walk(events)

print("SHOW DATES IN SAVED RESPONSE:")
for d, count in sorted(dates.items()):
    print(d, "=>", count, "showtimes")

print()
print("SEPTEMBER 24:", dates.get("20260924", 0))
print("SEPTEMBER 21:", dates.get("20260921", 0))

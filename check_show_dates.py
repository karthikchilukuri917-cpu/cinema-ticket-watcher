from app.providers.public_page import PublicPageFetcher
from app.providers.bookmyshow_html import BookMyShowHTMLParser
from datetime import date

url = "https://in.bookmyshow.com/cinemas/HYDERABAD/pvr-icon-hitech-madhapur-hyderabad/buytickets/PVHM/20260924"

html = PublicPageFetcher().fetch(url).html
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

print("SHOW DATES FOUND:")
for d, count in sorted(dates.items()):
    print(d, "=>", count, "showtimes")

print()
print("20260924 SHOWTIMES:", dates.get("20260924", 0))

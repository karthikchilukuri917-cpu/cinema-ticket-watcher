from app.providers.public_page import PublicPageFetcher
from app.providers.bookmyshow_html import BookMyShowHTMLParser
from datetime import date
import re
import json

url = "https://in.bookmyshow.com/cinemas/HYDERABAD/pvr-icon-hitech-madhapur-hyderabad/buytickets/PVHM/20260924"

html = PublicPageFetcher().fetch(url).html

print("HTML LENGTH:", len(html))
print("HAS 20260924:", "20260924" in html)

parser = BookMyShowHTMLParser()

event_data = parser._extract_event_array(html)

print("EVENT ARRAY:", "FOUND" if event_data is not None else "NOT FOUND")

if event_data is not None:
    print("EVENT COUNT:", len(event_data))

    for i, event in enumerate(event_data[:10]):
        if not isinstance(event, dict):
            continue

        print("\n========== EVENT", i, "==========")
        print("EventTitle:", event.get("EventTitle"))

        children = event.get("ChildEvents", [])

        print("ChildEvents:", len(children) if isinstance(children, list) else type(children))

        if isinstance(children, list):
            for j, child in enumerate(children[:10]):
                if not isinstance(child, dict):
                    continue

                print("\n  Child", j)
                print("  EventName:", child.get("EventName"))

                showtimes = child.get("ShowTimes", [])

                print("  ShowTimes:", len(showtimes) if isinstance(showtimes, list) else type(showtimes))

                if isinstance(showtimes, list):
                    for k, show in enumerate(showtimes[:20]):
                        if isinstance(show, dict):
                            print(
                                "   ",
                                k,
                                "| DateTime:", show.get("ShowDateTime"),
                                "| Time:", show.get("ShowTime"),
                                "| Status:", show.get("AvailStatus"),
                                "| Seats:", show.get("BestAvailableSeats"),
                                "| Session:", show.get("SessionId"),
                            )

shows = parser.parse(
    html=html,
    movie="Resident Evil",
    show_date=date(2026, 9, 24),
    cinema="PVR",
)

print("\n================================")
print("FINAL PARSED SHOWS:", len(shows))
print("================================")

for show in shows:
    print(show)

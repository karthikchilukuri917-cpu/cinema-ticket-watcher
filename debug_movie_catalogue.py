from app.cinemas import BookMyShowCinemaResolver
from app.providers.public_page import PublicPageFetcher


TARGET_DATE = "2026-09-25"


def inspect(fetcher, label, url):
    print("\n" + "=" * 80)
    print(label)
    print("=" * 80)

    print("URL:")
    print(url)

    response = fetcher.fetch(url)

    print("STATUS:", response.status_code)
    print("HTML LENGTH:", len(response.html))

    html = response.html

    checks = [
        "Event",
        "EventTitle",
        "EventName",
        "ShowTimes",
        "ShowDatesArray",
        "__INITIAL_STATE__",
        "captcha",
        "cloudflare",
    ]

    for value in checks:
        print(
            f"{value}:",
            value.lower() in html.lower(),
        )

    print("\nTITLE:")

    start = html.lower().find("<title>")
    end = html.lower().find("</title>")

    if start != -1 and end != -1:
        print(
            html[start + 7:end].strip()
        )
    else:
        print("NO TITLE FOUND")


def main():

    fetcher = PublicPageFetcher()

    # ---------------------------------------------------------
    # Known-good PVR page from our previous BookMyShow test
    # ---------------------------------------------------------

    inspect(
        fetcher,
        "KNOWN GOOD PVR",
        (
            "https://in.bookmyshow.com/cinemas/"
            "HYDERABAD/"
            "pvr-nexus-mall-kukatpally-hyderabad/"
            "buytickets/"
            "PVFS/"
            f"{TARGET_DATE}"
        ),
    )

    # ---------------------------------------------------------
    # Resolver result
    # ---------------------------------------------------------

    resolver = BookMyShowCinemaResolver()

    cinemas = resolver.discover("Hyderabad")

    print("\n" + "=" * 80)
    print("SEARCHING DISCOVERED CINEMAS FOR PVR")
    print("=" * 80)

    for cinema in cinemas:

        if "pvr" not in cinema.name.lower():
            continue

        print("\nFOUND:")
        print("Name:", cinema.name)
        print("Provider:", cinema.provider_id)
        print("Slug:", cinema.slug)
        print("City:", cinema.city_code)

        url = (
            "https://in.bookmyshow.com/cinemas/"
            "HYDERABAD/"
            f"{cinema.slug}/"
            "buytickets/"
            f"{cinema.provider_id}/"
            f"{TARGET_DATE}"
        )

        inspect(
            fetcher,
            cinema.name,
            url,
        )

        # Only inspect the first PVR
        break


if __name__ == "__main__":
    main()
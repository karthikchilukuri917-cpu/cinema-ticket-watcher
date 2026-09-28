import json

from app.providers.public_page import PublicPageFetcher


URL = (
    "https://in.bookmyshow.com/cinemas/"
    "HYDERABAD/"
    "pvr-nexus-mall-kukatpally-hyderabad/"
    "buytickets/PVFS/2026-09-25"
)


def extract_initial_state(html):
    marker = "window.__INITIAL_STATE__ = "

    start = html.find(marker)

    if start == -1:
        raise RuntimeError(
            "__INITIAL_STATE__ marker not found"
        )

    start += len(marker)

    decoder = json.JSONDecoder()

    state, _ = decoder.raw_decode(
        html[start:]
    )

    return state


def main():

    fetcher = PublicPageFetcher()

    response = fetcher.fetch(URL)

    print("STATUS:", response.status_code)
    print("HTML LENGTH:", len(response.html))

    state = extract_initial_state(
        response.html
    )

    data = state.get(
        "fetchVenuesListingApi"
    )

    print("\n" + "=" * 80)
    print("fetchVenuesListingApi")
    print("=" * 80)

    if data is None:
        print("NOT FOUND")
        return

    print(
        "TYPE:",
        type(data).__name__,
    )

    if isinstance(data, dict):

        print("\nTOP-LEVEL KEYS:")

        for key, value in data.items():

            print(
                f"  {key}: "
                f"{type(value).__name__}"
            )

            if isinstance(value, dict):
                print(
                    "    keys:",
                    list(value.keys())[:30],
                )

            elif isinstance(value, list):
                print(
                    "    length:",
                    len(value),
                )

    print("\n" + "=" * 80)
    print("RAW SUBTREE")
    print("=" * 80)

    print(
        json.dumps(
            data,
            indent=2,
            ensure_ascii=False,
        )[:20000]
    )


if __name__ == "__main__":
    main()
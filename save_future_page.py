from app.providers.public_page import PublicPageFetcher

url = "https://in.bookmyshow.com/cinemas/HYDERABAD/pvr-icon-hitech-madhapur-hyderabad/buytickets/PVHM/20260924"

try:
    response = PublicPageFetcher().fetch(url)

    with open(r"data\debug_pvr_20260924.html", "w", encoding="utf-8") as f:
        f.write(response.html)

    print("STATUS:", response.status_code)
    print("HTML LENGTH:", len(response.html))
    print("SAVED: data\debug_pvr_20260924.html")

except Exception as e:
    print("FETCH FAILED:", type(e).__name__, str(e))

from app.cinemas import BookMyShowCinemaResolver

resolver = BookMyShowCinemaResolver()

url = "https://in.bookmyshow.com/hyderabad/cinemas"
response = resolver._get(url)

print("STATUS:", response.status_code)
print("HTML LENGTH:", len(response.text))

html = response.text

print("cinemas/:", html.lower().count("/cinemas/"))
print("ART:", "art" in html.lower())
print("SHIVA:", "shiva" in html.lower())
print("GANGA:", "ganga" in html.lower())

with open(
    "data/hyderabad_cinemas_raw.html",
    "w",
    encoding="utf-8",
) as file:
    file.write(html)

print("SAVED: data/hyderabad_cinemas_raw.html")

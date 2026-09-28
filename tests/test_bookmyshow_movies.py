from app.providers.bookmyshow_movies import BookMyShowMovieProvider


def test_extract_movies_uses_json_ld_item_list():
    html = """
    <html>
    <head>
        <script type="application/ld+json">
        {
            "@context": "https://schema.org",
            "@type": "ItemList",
            "name": "Movies",
            "numberOfItems": 2,
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": 1,
                    "url": "https://in.bookmyshow.com/hyderabad/movies/the-paradise/ET00436621",
                    "name": "The Paradise"
                },
                {
                    "@type": "ListItem",
                    "position": 2,
                    "url": "https://in.bookmyshow.com/hyderabad/movies/devara-part-1/ET00310216",
                    "name": "Devara - Part 1"
                }
            ]
        }
        </script>
    </head>

    <body>
        <!-- This link must NOT be selected by the movie catalogue parser. -->
        <a href="/movies/footer-only-movie/ET99999999">
            Footer Only Movie
        </a>
    </body>
    </html>
    """

    provider = BookMyShowMovieProvider()

    movies = provider._extract_movies(html)

    assert len(movies) == 2

    assert movies[0].title == "The Paradise"
    assert movies[0].event_code == "ET00436621"
    assert movies[0].event_url == (
        "https://in.bookmyshow.com/hyderabad/movies/"
        "the-paradise/ET00436621"
    )

    assert movies[1].title == "Devara - Part 1"
    assert movies[1].event_code == "ET00310216"

    assert all(
        movie.event_code != "ET99999999"
        for movie in movies
    )
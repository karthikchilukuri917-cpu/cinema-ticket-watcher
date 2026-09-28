from contextlib import asynccontextmanager
from datetime import date
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

load_dotenv()
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.providers.bookmyshow_movies import BookMyShowMovieProvider
from app.cinemas import BookMyShowCinemaResolver
from app.config import (
    get_max_cycles,
    get_source_name,
)
from app.models import Watch
from app.runtime import watch_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Start all active watches when the API starts.

    The same process owns both the API and the
    background watch scheduler.
    """

    max_cycles = get_max_cycles()

    watch_service.scheduler.start_all(
        max_cycles=max_cycles,
    )

    try:
        yield

    finally:
        watch_service.scheduler.stop_all()


app = FastAPI(
    title="Cinema Ticket Watcher API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# Request Models
# =========================================================


class WatchCreateRequest(BaseModel):
    movie: str
    movie_event_code: str | None = None
    target_date: date
    city: str
    cinemas: list[str]


class WatchUpdateRequest(BaseModel):
    movie: str | None = None
    movie_event_code: str | None = None
    target_date: date | None = None
    city: str | None = None
    cinemas: list[str] | None = None


# =========================================================
# Response Models
# =========================================================


class WatchResponse(BaseModel):
    id: str
    movie: str
    movie_event_code: str | None = None
    target_date: date
    city: str
    cinemas: list[str]
    active: bool
    running: bool
    completed: bool


class HealthResponse(BaseModel):
    status: str
    source: str
    watches: int
    running_watches: int


class CinemaVenueResponse(BaseModel):
    name: str
    city: str
    provider_id: str
    slug: str
    city_code: str


class CinemaCatalogueResponse(BaseModel):
    city: str
    cinemas: list[CinemaVenueResponse]


class MovieCandidateResponse(BaseModel):
    title: str
    event_name: str
    event_code: str
    event_url: str | None = None
    event_group: str | None = None
    language: str | None = None
    dimension: str | None = None


class WatchHealthResponse(BaseModel):
    last_checked: str | None = None
    status: str | None = None
    message: str | None = None


class WatchStatusResponse(BaseModel):
    id: str
    active: bool
    running: bool
    completed: bool
    health: WatchHealthResponse
    availability: dict


class HistoryEvent(BaseModel):
    timestamp: str
    cinema: str
    show_time: str

    # The first observation of a show has no
    # previous status, so this must allow None.
    previous: str | None = None

    current: str
    previous_tickets: int | None = None
    current_tickets: int | None = None
    show_id: str | None = None


class WatchHistoryResponse(BaseModel):
    watch_id: str
    events: list[HistoryEvent]


# =========================================================
# Helpers
# =========================================================


def watch_to_response(
    watch_id: str,
    watch: Watch,
) -> dict:

    return {
        "id": watch_id,
        "movie": watch.movie,
        "movie_event_code": watch.movie_event_code,
        "target_date": watch.target_date,
        "city": watch.city,
        "cinemas": watch.cinemas,
        "active": watch.active,
        "running": (
            watch_service.scheduler.is_running(
                watch_id
            )
        ),
        "completed": watch.completed,
    }


def get_existing_watch(
    watch_id: str,
):

    record = watch_service.get_watch(
        watch_id.strip()
    )

    if record is None:

        raise HTTPException(
            status_code=404,
            detail="Watch not found.",
        )

    return record


# =========================================================
# Root
# =========================================================


@app.get("/")
def root():

    return {
        "name": "Cinema Ticket Watcher API",
        "status": "running",
    }


# =========================================================
# Health
# =========================================================


@app.get(
    "/health",
    response_model=HealthResponse,
)
def health():

    records = watch_service.list_watches()

    running_watch_ids = (
        watch_service.scheduler.running_watch_ids()
    )

    return {
        "status": "healthy",
        "source": get_source_name(),
        "watches": len(records),
        "running_watches": len(
            running_watch_ids
        ),
    }


# =========================================================
# Watches
# =========================================================


@app.get(
    "/watches",
    response_model=list[WatchResponse],
)
def list_watches():

    records = watch_service.list_watches()

    return [
        watch_to_response(
            record.watch_id,
            record.watch,
        )
        for record in records
    ]


@app.get(
    "/cinemas/{city}",
    response_model=CinemaCatalogueResponse,
)
def get_cinemas(city: str):
    city = city.strip()

    if not city:
        raise HTTPException(
            status_code=400,
            detail="City cannot be empty.",
        )

    try:
        resolver = BookMyShowCinemaResolver()
        venues = resolver.discover(city)

    except ValueError as error:
        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return {
        "city": city,
        "cinemas": [
            {
                "name": venue.name,
                "city": venue.city,
                "provider_id": venue.provider_id,
                "slug": venue.slug,
                "city_code": venue.city_code,
            }
            for venue in venues
        ],
    }


@app.get(
    "/movies/{city}/{target_date}",
    response_model=list[MovieCandidateResponse],
)
def get_movies(
    city: str,
    target_date: date,
):
    city = city.strip()

    if not city:
        raise HTTPException(
            status_code=400,
            detail="City cannot be empty.",
        )

    try:
        provider = BookMyShowMovieProvider()

        result = provider.get_movies(
            city=city,
            target_date=target_date.isoformat(),
        )

    except RuntimeError as error:
        raise HTTPException(
            status_code=502,
            detail=str(error),
        ) from error

    return [
        {
            "title": movie.title,
            "event_name": movie.event_name,
            "event_code": movie.event_code,
            "event_url": movie.event_url,
            "event_group": movie.event_group,
            "language": movie.language,
            "dimension": movie.dimension,
        }
        for movie in result.movies
    ]


@app.post(
    "/watches",
    response_model=WatchResponse,
    status_code=201,
)
def create_watch(
    request: WatchCreateRequest,
):

    watch_id = uuid4().hex

    try:

        watch = Watch(
            movie=request.movie,
            movie_event_code=request.movie_event_code,
            target_date=request.target_date,
            city=request.city,
            cinemas=request.cinemas,
        )

        created = watch_service.create_watch(
            watch_id=watch_id,
            watch=watch,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    return watch_to_response(
        watch_id,
        created,
    )


@app.get(
    "/watches/{watch_id}",
    response_model=WatchResponse,
)
def get_watch(
    watch_id: str,
):

    record = get_existing_watch(
        watch_id
    )

    return watch_to_response(
        record.watch_id,
        record.watch,
    )


# =========================================================
# Watch Status
# =========================================================


@app.get(
    "/watches/{watch_id}/status",
    response_model=WatchStatusResponse,
)
def get_watch_status(
    watch_id: str,
):

    record = get_existing_watch(
        watch_id
    )

    availability = (
        watch_service.get_watch_state(
            record.watch_id
        )
    )

    health = (
        watch_service.get_watch_health(
            record.watch_id
        )
    )

    return {
        "id": record.watch_id,
        "active": record.watch.active,
        "running": (
            watch_service.scheduler.is_running(
                record.watch_id
            )
        ),
        "completed": record.watch.completed,
        "health": health,
        "availability": availability,
    }


# =========================================================
# Watch History
# =========================================================


@app.get(
    "/watches/{watch_id}/history",
    response_model=WatchHistoryResponse,
)
def get_watch_history(
    watch_id: str,
):

    record = get_existing_watch(
        watch_id
    )

    events = (
        watch_service.get_watch_history(
            record.watch_id
        )
    )

    return {
        "watch_id": record.watch_id,
        "events": events,
    }


# =========================================================
# Update Watch
# =========================================================


@app.patch(
    "/watches/{watch_id}",
    response_model=WatchResponse,
)
def update_watch(
    watch_id: str,
    request: WatchUpdateRequest,
):

    watch_id = watch_id.strip()

    record = get_existing_watch(
        watch_id
    )

    current_watch = record.watch

    updated = Watch(
        movie=(
            request.movie
            if request.movie is not None
            else current_watch.movie
        ),
        movie_event_code=(
            request.movie_event_code
            if request.movie_event_code is not None
            else current_watch.movie_event_code
        ),
        target_date=(
            request.target_date
            if request.target_date is not None
            else current_watch.target_date
        ),
        city=(
            request.city
            if request.city is not None
            else current_watch.city
        ),
        cinemas=(
            request.cinemas
            if request.cinemas is not None
            else current_watch.cinemas
        ),
        active=current_watch.active,
        completed=current_watch.completed,
    )

    try:

        saved = watch_service.update_watch(
            watch_id=watch_id,
            watch=updated,
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    return watch_to_response(
        watch_id,
        saved,
    )


# =========================================================
# Delete Watch
# =========================================================


@app.delete(
    "/watches/{watch_id}",
    status_code=204,
)
def delete_watch(
    watch_id: str,
):

    watch_id = watch_id.strip()

    try:

        deleted = watch_service.delete_watch(
            watch_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    if not deleted:

        raise HTTPException(
            status_code=404,
            detail="Watch not found.",
        )


# =========================================================
# Pause
# =========================================================


@app.post(
    "/watches/{watch_id}/pause",
    response_model=WatchResponse,
)
def pause_watch(
    watch_id: str,
):

    watch_id = watch_id.strip()

    try:

        paused = watch_service.pause_watch(
            watch_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    return watch_to_response(
        watch_id,
        paused,
    )


# =========================================================
# Resume
# =========================================================


@app.post(
    "/watches/{watch_id}/resume",
    response_model=WatchResponse,
)
def resume_watch(
    watch_id: str,
):

    watch_id = watch_id.strip()

    try:

        resumed = watch_service.resume_watch(
            watch_id
        )

    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error),
        ) from error

    except RuntimeError as error:

        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    return watch_to_response(
        watch_id,
        resumed,
    )
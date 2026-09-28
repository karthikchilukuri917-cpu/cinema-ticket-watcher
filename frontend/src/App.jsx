import { useEffect, useMemo, useState } from "react";
import {
  getWatches,
  getWatch,
  getWatchStatus,
  getWatchHistory,
  getCinemas,
  getMovies,
  createWatch,
  updateWatch,
  pauseWatch,
  resumeWatch,
  deleteWatch,
} from "./api";
import "./App.css";

const EMPTY_FORM = {
  movie: "",
  target_date: "",
  city: "",
  cinemas: "",
};

const STATUS_POLL_INTERVAL = 10000;

function getTodayDate() {
  const today = new Date();

  const year = today.getFullYear();
  const month = String(
    today.getMonth() + 1,
  ).padStart(2, "0");
  const day = String(
    today.getDate(),
  ).padStart(2, "0");

  return `${year}-${month}-${day}`;
}

function App() {
  const [watches, setWatches] = useState([]);
  const [availability, setAvailability] =
    useState({});
  const [statusLoading, setStatusLoading] =
    useState({});
  const [lastCheckedAt, setLastCheckedAt] =
    useState({});
  const [currentTime, setCurrentTime] =
    useState(Date.now());
  const [loading, setLoading] = useState(true);

  const [selectedWatch, setSelectedWatch] =
    useState(null);

  const [history, setHistory] = useState({});
  const [historyLoading, setHistoryLoading] =
    useState({});
  const [historyError, setHistoryError] =
    useState({});

  const [showForm, setShowForm] =
    useState(false);

  const [form, setForm] =
    useState(EMPTY_FORM);

  const [cinemaCatalogue, setCinemaCatalogue] =
    useState([]);

  const [cinemaSearch, setCinemaSearch] =
    useState("");

  const [selectedCinemas, setSelectedCinemas] =
    useState([]);

  const [cinemaLoading, setCinemaLoading] =
    useState(false);

  const [cinemaError, setCinemaError] =
    useState("");

  const [cinemaCatalogueCity, setCinemaCatalogueCity] =
    useState("");

  const [movieCatalogue, setMovieCatalogue] =
    useState([]);

  const [movieSearch, setMovieSearch] =
    useState("");

  const [selectedMovie, setSelectedMovie] =
    useState(null);

  const [movieLoading, setMovieLoading] =
    useState(false);

  const [movieError, setMovieError] =
    useState("");

  const [movieCatalogueKey, setMovieCatalogueKey] =
    useState("");

  const [creating, setCreating] =
    useState(false);

  const [error, setError] =
    useState("");

  const [actionLoading, setActionLoading] =
    useState(null);

  const [filter, setFilter] =
    useState("all");

  async function loadWatches() {
    try {
      setError("");

      const data = await getWatches();

      setWatches(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  async function loadWatchStatus(watchId) {
    setStatusLoading((current) => ({
      ...current,
      [watchId]: true,
    }));

    try {
      const data =
        await getWatchStatus(watchId);

      setAvailability((current) => ({
        ...current,
        [watchId]:
          data.availability ?? {},
      }));

      // --------------------------------------------------
      // Keep the frontend lifecycle state synchronized
      // with the backend.
      //
      // This is important when WatchScheduler automatically
      // completes a watch after tickets become available.
      // --------------------------------------------------
      setWatches((current) =>
        current.map((watch) =>
          watch.id === watchId
            ? {
                ...watch,
                active:
                  data.active ??
                  watch.active,
                running:
                  data.running ??
                  watch.running,
                completed:
                  data.completed ??
                  watch.completed,
              }
            : watch,
        ),
      );

      // Keep the open details modal synchronized too.
      setSelectedWatch((current) =>
        current &&
        current.id === watchId
          ? {
              ...current,
              active:
                data.active ??
                current.active,
              running:
                data.running ??
                current.running,
              completed:
                data.completed ??
                current.completed,
            }
          : current,
      );

      setLastCheckedAt((current) => ({
        ...current,
        [watchId]: Date.now(),
      }));
    } catch {
      setAvailability((current) => ({
        ...current,
        [watchId]: null,
      }));
    } finally {
      setStatusLoading((current) => ({
        ...current,
        [watchId]: false,
      }));
    }
  }

  async function loadWatchHistory(watchId) {
    setHistoryLoading((current) => ({
      ...current,
      [watchId]: true,
    }));

    setHistoryError((current) => ({
      ...current,
      [watchId]: "",
    }));

    try {
      const data =
        await getWatchHistory(watchId);

      setHistory((current) => ({
        ...current,
        [watchId]: data.events ?? [],
      }));
    } catch (err) {
      setHistoryError((current) => ({
        ...current,
        [watchId]:
          err.message ||
          "Failed to load history.",
      }));
    } finally {
      setHistoryLoading((current) => ({
        ...current,
        [watchId]: false,
      }));
    }
  }

  async function loadAllStatuses(
    watchList = watches,
  ) {
    if (!watchList.length) {
      return;
    }

    await Promise.all(
      watchList.map((watch) =>
        loadWatchStatus(watch.id),
      ),
    );
  }

  const watchIds = watches
    .map((watch) => watch.id)
    .join(",");

  useEffect(() => {
    loadWatches();
  }, []);

  useEffect(() => {
    const city = form.city.trim();
    const targetDate = form.target_date;

    if (!city || !targetDate) {
      return undefined;
    }

    const timer = setTimeout(() => {
      loadMovieCatalogue(city, targetDate);
    }, 450);

    return () => {
      clearTimeout(timer);
    };
  }, [form.city, form.target_date]);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);

    return () => {
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!watches.length) {
      return undefined;
    }

    // Initial status check.
    loadAllStatuses(watches);

    // Continue checking every 10 seconds.
    const interval = setInterval(() => {
      loadAllStatuses(watches);
    }, STATUS_POLL_INTERVAL);

    return () => {
      clearInterval(interval);
    };
  }, [watchIds]);

  useEffect(() => {
    function handleEscape(event) {
      if (
        event.key === "Escape" &&
        selectedWatch
      ) {
        setSelectedWatch(null);
      }
    }

    window.addEventListener(
      "keydown",
      handleEscape,
    );

    return () => {
      window.removeEventListener(
        "keydown",
        handleEscape,
      );
    };
  }, [selectedWatch]);

  function handleChange(event) {
    const {
      name,
      value,
    } = event.target;

    setForm((current) => ({
      ...current,
      [name]: value,
    }));

    if (name === "city") {
      setCinemaCatalogue([]);
      setSelectedCinemas([]);
      setCinemaSearch("");
      setCinemaError("");
      setCinemaCatalogueCity("");
    }

    if (name === "city" || name === "target_date") {
      setMovieCatalogue([]);
      setMovieSearch("");
      setSelectedMovie(null);
      setMovieCatalogueKey("");
      setMovieError("");
    }
  }

  async function loadCinemaCatalogue(city) {
    const normalizedCity = city.trim();

    setCinemaCatalogue([]);
    setSelectedCinemas([]);
    setCinemaSearch("");
    setCinemaError("");
    setCinemaCatalogueCity("");

    if (!normalizedCity) {
      return;
    }

    setCinemaLoading(true);

    try {
      const data =
        await getCinemas(normalizedCity);

      setCinemaCatalogue(
        data.cinemas ?? [],
      );

      setCinemaCatalogueCity(
        data.city ?? normalizedCity,
      );
    } catch (err) {
      setCinemaError(
        err.message ||
          `Requested theatre catalogue is not available for ${normalizedCity}.`,
      );
    } finally {
      setCinemaLoading(false);
    }
  }

  async function loadMovieCatalogue(
    city,
    targetDate,
  ) {
    if (!city || !targetDate) {
      setMovieCatalogue([]);
      setMovieCatalogueKey("");
      return;
    }

    const key = `${city.trim()}|${targetDate}`;

    if (key === movieCatalogueKey) {
      return;
    }

    setMovieLoading(true);
    setMovieError("");

    try {
      const movies = await getMovies(
        city.trim(),
        targetDate,
      );

      setMovieCatalogue(movies);
      setMovieCatalogueKey(key);
    } catch (error) {
      setMovieCatalogue([]);
      setMovieCatalogueKey("");
      setMovieError(
        error.message ||
          "Unable to load movies.",
      );
    } finally {
      setMovieLoading(false);
    }
  }

  function selectCinema(cinema) {
    const alreadySelected =
      selectedCinemas.some(
        (selected) =>
          selected.provider_id ===
          cinema.provider_id,
      );

    if (alreadySelected) {
      return;
    }

    setSelectedCinemas(
      (current) => [
        ...current,
        cinema,
      ],
    );

    setCinemaSearch("");
  }

  async function handleSubmit(event) {
    event.preventDefault();

    setError("");

    const city = form.city.trim();
    const targetDate = form.target_date;

    const cinemas =
      selectedCinemas.map(
        (cinema) => cinema.name,
      );

    if (!selectedMovie) {
      setError("Please select a movie from the catalogue.");
      return;
    }

    if (!city) {
      setError("Please enter a city.");
      return;
    }

    if (!targetDate) {
      setError("Please select a target date.");
      return;
    }

    if (targetDate < getTodayDate()) {
      setError(
        "Target date cannot be in the past.",
      );
      return;
    }

    if (selectedCinemas.length === 0) {
      setError(
        "Please select at least one cinema from the BookMyShow results.",
      );
      return;
    }

    setCreating(true);

    try {
      const payload = {
        ...form,
        movie: selectedMovie.title,
        movie_event_code:
          selectedMovie.event_code,
        cinemas,
      };

      const created =
        await createWatch(payload);

      setWatches((current) => [
        ...current,
        created,
      ]);

      setForm(EMPTY_FORM);
      setShowForm(false);
    } catch (err) {
      setError(
        err.message ||
          "Failed to create watch.",
      );
    } finally {
      setCreating(false);
    }
  }

  async function handlePause(watchId) {
    setActionLoading(watchId);
    setError("");

    try {
      const updated =
        await pauseWatch(watchId);

      setWatches((current) =>
        current.map((watch) =>
          watch.id === watchId
            ? updated
            : watch,
        ),
      );

      setSelectedWatch((current) =>
        current &&
        current.id === watchId
          ? updated
          : current,
      );

      await loadWatchStatus(watchId);
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  }

  async function handleResume(watchId) {
    setActionLoading(watchId);
    setError("");

    try {
      const updated =
        await resumeWatch(watchId);

      setWatches((current) =>
        current.map((watch) =>
          watch.id === watchId
            ? updated
            : watch,
        ),
      );

      setSelectedWatch((current) =>
        current &&
        current.id === watchId
          ? updated
          : current,
      );

      await loadWatchStatus(watchId);
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  }

  async function handleDelete(watchId) {
    const confirmed =
      window.confirm(
        "Delete this watch permanently?",
      );

    if (!confirmed) {
      return;
    }

    setActionLoading(watchId);
    setError("");

    try {
      await deleteWatch(watchId);

      setWatches((current) =>
        current.filter(
          (watch) =>
            watch.id !== watchId,
        ),
      );

      setAvailability((current) => {
        const next = {
          ...current,
        };

        delete next[watchId];

        return next;
      });

      setLastCheckedAt((current) => {
        const next = {
          ...current,
        };

        delete next[watchId];

        return next;
      });

      setHistory((current) => {
        const next = {
          ...current,
        };

        delete next[watchId];

        return next;
      });

      if (
        selectedWatch?.id === watchId
      ) {
        setSelectedWatch(null);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setActionLoading(null);
    }
  }

  function getAvailableShows(watchId) {
    const watchAvailability =
      availability[watchId];

    if (!watchAvailability) {
      return [];
    }

    return Object.values(
      watchAvailability,
    )
      .filter(
        (show) =>
          show &&
          typeof show === "object" &&
          show.status === "AVAILABLE",
      )
      .map((show) => ({
        cinema: show.cinema,
        time: show.show_time,
        availableTickets:
          show.available_tickets,
        sourceId: show.source_id,
      }));
  }

  function getTotalAvailableTickets(watchId) {
    const shows = getAvailableShows(watchId);

    if (!shows.length) {
      return {
        total: null,
        complete: false,
      };
    }

    let total = 0;
    let hasUnknown = false;

    shows.forEach((show) => {
      if (
        typeof show.availableTickets ===
        "number" &&
        Number.isFinite(
          show.availableTickets,
        )
      ) {
        total += show.availableTickets;
      } else {
        hasUnknown = true;
      }
    });

    return {
      total,
      complete: !hasUnknown,
    };
  }

  function hasTickets(watchId) {
    return (
      getAvailableShows(watchId)
        .length > 0
    );
  }

  const filteredCinemas = useMemo(() => {
    const query =
      cinemaSearch.trim().toLowerCase();

    if (!query) {
      return [];
    }

    return cinemaCatalogue
      .filter((cinema) =>
        String(cinema.name ?? "")
          .toLowerCase()
          .includes(query),
      )
      .sort((a, b) => {
        const aName =
          String(a.name ?? "").toLowerCase();
        const bName =
          String(b.name ?? "").toLowerCase();

        const aStarts =
          aName.startsWith(query);

        const bStarts =
          bName.startsWith(query);

        if (aStarts && !bStarts) {
          return -1;
        }

        if (!aStarts && bStarts) {
          return 1;
        }

        return aName.localeCompare(
          bName,
        );
      });
  }, [
    cinemaCatalogue,
    cinemaSearch,
  ]);

  const filteredMovies = movieCatalogue
    .filter((movie) =>
      movie.title
        .toLowerCase()
        .includes(
          movieSearch.trim().toLowerCase(),
        ),
    )
    .sort((a, b) => {
      const query =
        movieSearch.trim().toLowerCase();

      if (!query) {
        return a.title.localeCompare(
          b.title,
        );
      }

      const aStarts = a.title
        .toLowerCase()
        .startsWith(query);
      const bStarts = b.title
        .toLowerCase()
        .startsWith(query);

      if (aStarts && !bStarts) {
        return -1;
      }

      if (!aStarts && bStarts) {
        return 1;
      }

      return a.title.localeCompare(
        b.title,
      );
    });

  const filteredWatches = useMemo(() => {
    if (filter === "available") {
      return watches.filter((watch) =>
        hasTickets(watch.id),
      );
    }

    if (filter === "waiting") {
      return watches.filter(
        (watch) =>
          !hasTickets(watch.id),
      );
    }

    return watches;
  }, [watches, availability, filter]);

  const availableWatchCount =
    watches.filter((watch) =>
      hasTickets(watch.id),
    ).length;

  const runningWatchCount =
    watches.filter(
      (watch) => watch.running,
    ).length;

  function formatDateParts(dateString) {
    if (!dateString) {
      return {
        day: "--",
        month: "",
        weekday: "",
      };
    }

    const date = new Date(
      `${dateString}T00:00:00`,
    );

    if (
      Number.isNaN(date.getTime())
    ) {
      return {
        day: dateString,
        month: "",
        weekday: "",
      };
    }

    return {
      day: date.toLocaleDateString(
        undefined,
        {
          day: "2-digit",
        },
      ),
      month: date.toLocaleDateString(
        undefined,
        {
          month: "long",
        },
      ),
      weekday: date.toLocaleDateString(
        undefined,
        {
          weekday: "long",
        },
      ),
    };
  }

  function getTargetDateLabel(
    dateString,
    nowTimestamp,
  ) {
    if (!dateString) {
      return "";
    }

    const targetDate = new Date(
      `${dateString}T00:00:00`,
    );

    if (
      Number.isNaN(
        targetDate.getTime(),
      )
    ) {
      return "";
    }

    const today = new Date(nowTimestamp);

    const todayStart = new Date(
      today.getFullYear(),
      today.getMonth(),
      today.getDate(),
    );

    const targetStart = new Date(
      targetDate.getFullYear(),
      targetDate.getMonth(),
      targetDate.getDate(),
    );

    const millisecondsPerDay =
      1000 * 60 * 60 * 24;

    const difference =
      Math.round(
        (targetStart.getTime() -
          todayStart.getTime()) /
          millisecondsPerDay,
      );

    if (difference < 0) {
      return "Date passed";
    }

    if (difference === 0) {
      return "Today";
    }

    if (difference === 1) {
      return "Tomorrow";
    }

    return `${difference} days away`;
  }

  function formatCheckedTime(watch) {
    const status =
      availability[watch.id];

    const checkedAt =
      lastCheckedAt[watch.id];

    if (
      statusLoading[watch.id] &&
      !checkedAt
    ) {
      return "Checking now";
    }

    if (status === null) {
      return checkedAt
        ? `Checked ${getElapsedTime(
            checkedAt,
          )} ago · retrying`
        : "Status unavailable";
    }

    if (!checkedAt) {
      return "Checking now";
    }

    return `Checked ${getElapsedTime(
      checkedAt,
    )} ago`;
  }

  function getElapsedTime(timestamp) {
    const elapsedMilliseconds =
      Math.max(
        0,
        currentTime - timestamp,
      );

    const elapsedSeconds =
      Math.floor(
        elapsedMilliseconds / 1000,
      );

    if (elapsedSeconds < 5) {
      return "just now";
    }

    if (elapsedSeconds < 60) {
      return `${elapsedSeconds}s`;
    }

    const elapsedMinutes =
      Math.floor(
        elapsedSeconds / 60,
      );

    if (elapsedMinutes < 60) {
      return `${elapsedMinutes}m`;
    }

    const elapsedHours =
      Math.floor(
        elapsedMinutes / 60,
      );

    if (elapsedHours < 24) {
      return `${elapsedHours}h`;
    }

    const elapsedDays =
      Math.floor(
        elapsedHours / 24,
      );

    return `${elapsedDays}d`;
  }

  function renderWatchCard(watch) {
    const busy =
      actionLoading === watch.id;

    const availableShows =
      getAvailableShows(watch.id);

    const ticketsAvailable =
      availableShows.length > 0;

    const watchCompleted =
      watch.completed === true;

    const isPaused =
      !watch.active &&
      !watchCompleted;

    const date =
      formatDateParts(
        watch.target_date,
      );

    const targetDateLabel =
      getTargetDateLabel(
        watch.target_date,
        currentTime,
      );

    return (
      <article
        className={`watch-card-new ${
          ticketsAvailable
            ? "tickets-open"
            : ""
        }`}
        key={watch.id}
        onClick={() =>
          openWatchDetails(watch)
        }
      >
        <div className="watch-date">
          <strong>
            {date.day}
          </strong>

          <span>
            {date.month}
          </span>

          <small>
            {date.weekday}
          </small>

          <em className="target-countdown">
            {targetDateLabel}
          </em>
        </div>

        <div className="watch-main">
          <h2>{watch.movie}</h2>

          <div className="watch-city">
            <span>⌾</span>
            {watch.city}
          </div>

          {ticketsAvailable ? (
            <div className="show-chips">
              {availableShows.map(
                (show, index) => (
                  <div
                    className="show-chip"
                    key={`${show.cinema}-${show.time}-${index}`}
                  >
                    <strong>
                      {show.time}
                    </strong>

                    <span>
                      {show.cinema}
                    </span>

                    {show.availableTickets !==
                      null &&
                      show.availableTickets !==
                        undefined && (
                        <b>
                          {
                            show.availableTickets
                          }{" "}
                          seats
                        </b>
                      )}
                  </div>
                ),
              )}
            </div>
          ) : (
            <div className="cinema-chips">
              {watch.cinemas.map(
                (cinema) => (
                  <span
                    key={cinema}
                  >
                    {cinema}
                  </span>
                ),
              )}
            </div>
          )}
        </div>

        <div className="watch-status-panel">
          <div
            className={`availability-label ${
              ticketsAvailable
                ? "open"
                : ""
            } ${
              isPaused
                ? "paused"
                : ""
            }`}
          >
            <span className="status-dot" />

            {watchCompleted
              ? "Tickets available"
              : isPaused
                ? "Paused"
                : ticketsAvailable
                  ? "Tickets available"
                  : "Watching"}
          </div>

          <strong className="status-title">
            {watchCompleted
              ? "Monitoring stopped"
              : isPaused
                ? "Monitoring paused"
                : ticketsAvailable
                  ? `${availableShows.length} ${
                      availableShows.length ===
                      1
                        ? "show"
                        : "shows"
                    } open`
                  : "No tickets yet"}
          </strong>

          <div className="watch-check-info">
            <span className="checked-text">
              {formatCheckedTime(watch)}
            </span>

            {!ticketsAvailable &&
              !isPaused && (
                <span className="polling-text">
                  Checks every 10s
                </span>
              )}
          </div>

          <div
            className="card-actions"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            {watch.active ? (
              <button
                className="pause-button"
                onClick={() =>
                  handlePause(
                    watch.id,
                  )
                }
                disabled={busy}
              >
                {busy
                  ? "..."
                  : "Ⅱ  Pause"}
              </button>
            ) : !watchCompleted ? (
              <button
                className="resume-button"
                onClick={() =>
                  handleResume(
                    watch.id,
                  )
                }
                disabled={busy}
              >
                {busy
                  ? "..."
                  : "▶  Resume"}
              </button>
            ) : null}

            <button
              className="delete-icon-button"
              onClick={() =>
                handleDelete(
                  watch.id,
                )
              }
              disabled={busy}
              aria-label="Delete watch"
            >
              ♧
            </button>
          </div>
        </div>
      </article>
    );
  }

  function renderModalAvailability(watch) {
    const watchStatus =
      availability[watch.id];

    const checking =
      statusLoading[watch.id];

    if (
      checking &&
      watchStatus === undefined
    ) {
      return (
        <div className="modal-status-box">
          Checking availability...
        </div>
      );
    }

    if (watchStatus === null) {
      return (
        <div className="modal-status-box">
          Status unavailable. The next
          automatic check will try again.
        </div>
      );
    }

    const shows =
      getAvailableShows(watch.id);

    const ticketSummary =
      getTotalAvailableTickets(watch.id);

    if (!shows.length) {
      return (
        <div className="modal-status-box">
          No tickets available yet.
        </div>
      );
    }

    return (
      <div className="modal-availability">
        <div className="availability-summary-box">
          <div className="availability-summary-main">
            <span className="availability-summary-label">
              {ticketSummary.complete
                ? "Total available tickets"
                : "Available shows"}
            </span>

            <strong className="availability-summary-value">
              {ticketSummary.complete
                ? ticketSummary.total
                : shows.length}
            </strong>
          </div>

          <p className="availability-summary-note">
            {ticketSummary.complete
              ? "Exact ticket count is available for all currently available shows."
              : "BookMyShow confirms these shows are available, but exact seat counts are not exposed for every show yet."}
          </p>
        </div>

        <div className="availability-show-count">
          {shows.length}{" "}
          {shows.length === 1
            ? "show"
            : "shows"}{" "}
          available
        </div>

        <div className="modal-show-list">
          {shows.map(
            (show, index) => (
              <div
                className="modal-show-row"
                key={`${show.cinema}-${show.time}-${index}`}
              >
                <div>
                  <span>
                    {show.cinema}
                  </span>

                  <strong>
                    {show.time}
                  </strong>
                </div>

                <span className="modal-show-availability">
                  {show.availableTickets !==
                    null &&
                  show.availableTickets !==
                    undefined
                    ? `${show.availableTickets} seats`
                    : "Available"}
                </span>
              </div>
            ),
          )}
        </div>
      </div>
    );
  }

  function formatHistoryTimestamp(
    timestamp,
  ) {
    if (!timestamp) {
      return "Unknown time";
    }

    const date =
      new Date(timestamp);

    if (
      Number.isNaN(date.getTime())
    ) {
      return timestamp;
    }

    return date.toLocaleString(
      undefined,
      {
        dateStyle: "medium",
        timeStyle: "short",
      },
    );
  }

  function renderHistory(watch) {
    const events =
      history[watch.id];

    if (
      historyLoading[watch.id]
    ) {
      return (
        <div className="history-empty">
          Loading detection history...
        </div>
      );
    }

    if (
      historyError[watch.id]
    ) {
      return (
        <div className="history-empty">
          {historyError[watch.id]}
        </div>
      );
    }

    if (
      !events ||
      events.length === 0
    ) {
      return (
        <div className="history-empty">
          No availability changes detected
          yet.
        </div>
      );
    }

    return (
      <div className="history-list">
        {[...events]
          .reverse()
          .map(
            (event, index) => (
              <div
                className="history-item"
                key={`${event.timestamp}-${index}`}
              >
                <div>
                  <strong>
                    {event.cinema}
                  </strong>

                  <span>
                    {event.show_time}
                  </span>
                </div>

                <div className="history-change">
                  <span>
                    {event.previous ||
                      "UNKNOWN"}
                  </span>

                  <b>→</b>

                  <span>
                    {event.current ||
                      "UNKNOWN"}
                  </span>
                </div>

                <time>
                  {formatHistoryTimestamp(
                    event.timestamp,
                  )}
                </time>
              </div>
            ),
          )}
      </div>
    );
  }

  function openWatchDetails(watch) {
    setSelectedWatch(watch);
    loadWatchHistory(watch.id);
  }

  async function refreshWatchDetails(
    watchId,
  ) {
    await Promise.all([
      loadWatchStatus(watchId),
      loadWatchHistory(watchId),
    ]);
  }

  // --------------------------------------------------
  // Keep the selected watch synchronized with the
  // latest watches state.
  //
  // This prevents the modal from showing an old
  // "Active" / "Paused" value after the backend
  // automatically completes a watch.
  // --------------------------------------------------
  const currentSelectedWatch =
    selectedWatch
      ? watches.find(
          (watch) =>
            watch.id ===
            selectedWatch.id,
        ) ?? selectedWatch
      : null;

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-icon">
            🎟
          </div>

          <span>
            Cinema Ticket Watcher
          </span>
        </div>

        <button
          className="new-watch-button"
          onClick={() =>
            setShowForm(true)
          }
        >
          <span>＋</span>
          New watch
        </button>
      </header>

      <main className="dashboard-new">
        <section className="hero">
          <div>
            <h1>
              Your watches
            </h1>

            <p>
              We check the theatres. You
              get first pick of the seats.
            </p>
          </div>

          <div className="watch-summary">
            <span
              className={
                availableWatchCount
                  ? "summary-available"
                  : ""
              }
            >
              <i />
              {availableWatchCount}{" "}
              has tickets
            </span>

            <span>
              {runningWatchCount} running
            </span>

            <span>
              {watches.length} total
            </span>
          </div>
        </section>

        <div className="filter-tabs">
          <button
            className={
              filter === "all"
                ? "active"
                : ""
            }
            onClick={() =>
              setFilter("all")
            }
          >
            All
          </button>

          <button
            className={
              filter === "available"
                ? "active"
                : ""
            }
            onClick={() =>
              setFilter("available")
            }
          >
            Tickets available
          </button>

          <button
            className={
              filter === "waiting"
                ? "active"
                : ""
            }
            onClick={() =>
              setFilter("waiting")
            }
          >
            Waiting
          </button>
        </div>

        {loading ? (
          <div className="dashboard-state">
            <div className="state-spinner" />
            <p>Loading your watches...</p>
          </div>
        ) : error ? (
          <div className="dashboard-state error-state">
            <p>{error}</p>
            <button
              className="retry-button"
              onClick={loadWatches}
            >
              Retry
            </button>
          </div>
        ) : filteredWatches.length === 0 ? (
          <div className="dashboard-state">
            <p>
              {filter === "all"
                ? "You don't have any watches yet."
                : filter === "available"
                  ? "No tickets are available right now."
                  : "No watches are waiting for tickets."}
            </p>

            {filter === "all" && (
              <button
                className="primary-button"
                onClick={() => {
                  setError("");
                  setShowForm(true);
                }}
              >
                Create your first watch
              </button>
            )}
          </div>
        ) : (
          <div className="watch-list-new">
            {filteredWatches.map(
              renderWatchCard,
            )}
          </div>
        )}

        {showForm && (
          <div
            className="modal-overlay"
            onClick={() =>
              setShowForm(false)
            }
          >
            <div
              className="form-modal"
              onClick={(event) =>
                event.stopPropagation()
              }
            >
              <div className="modal-header">
                <div>
                  <h2>
                    New watch
                  </h2>

                  <p>
                    Tell us what movie
                    you're waiting for.
                  </p>
                </div>

                <button
                  className="modal-close"
                  onClick={() =>
                    setShowForm(false)
                  }
                >
                  ×
                </button>
              </div>

              <form
                className="watch-form-new"
                onSubmit={handleSubmit}
              >
                <label>
                  City
                  <input
                    name="city"
                    value={form.city}
                    onChange={
                      handleChange
                    }
                    placeholder="Hyderabad"
                    required
                  />
                </label>

                <label>
                  Target date
                  <input
                    type="date"
                    name="target_date"
                    value={
                      form.target_date
                    }
                    onChange={
                      handleChange
                    }
                    min={getTodayDate()}
                    required
                  />
                </label>


                <div className="field">
                  <label>Movie</label>

                  <div className="movie-search-row">
                    <input
                      type="text"
                      placeholder={
                        form.city && form.target_date
                          ? "Search movies from BookMyShow..."
                          : "Enter city and date first"
                      }
                      value={movieSearch}
                      disabled={
                        !form.city ||
                        !form.target_date
                      }
                      onChange={(event) => {
                        const value =
                          event.target.value;

                        setMovieSearch(value);

                        if (
                          selectedMovie &&
                          value !== selectedMovie.title
                        ) {
                          setSelectedMovie(null);
                          setForm((current) => ({
                            ...current,
                            movie: "",
                          }));
                        }
                      }}
                      onFocus={() => {
                        if (
                          form.city &&
                          form.target_date
                        ) {
                          loadMovieCatalogue(
                            form.city,
                            form.target_date,
                          );
                        }
                      }}
                    />

                  </div>

                  {movieLoading && (
                    <div className="search-status">
                      Loading movies from BookMyShow...
                    </div>
                  )}

                  {movieError && (
                    <div className="search-error">
                      {movieError}
                    </div>
                  )}

                  {!selectedMovie &&
                    movieCatalogue.length > 0 &&
                    filteredMovies.length > 0 && (
                      <div className="search-results">
                        {filteredMovies.map((movie) => (
                          <button
                            type="button"
                            key={
                              movie.event_code ||
                              `${movie.title}-${movie.provider_id || "movie"}`
                            }
                            className="search-result-item"
                            onClick={() => {
                              setSelectedMovie(movie);
                              setMovieSearch(
                                movie.title,
                              );

                              setForm((current) => ({
                                ...current,
                                movie: movie.title,
                              }));
                            }}
                          >
                            <span>
                              {movie.title}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}

                  {movieSearch &&
                    !selectedMovie &&
                    !movieLoading &&
                    movieCatalogue.length > 0 &&
                    filteredMovies.length === 0 && (
                      <div className="search-empty">
                        Movie not found in BookMyShow's{" "}
                        {form.city} catalogue.
                      </div>
                    )}

                  {selectedMovie && (
                    <div className="selected-movie">
                      <span>
                        {selectedMovie.title}
                      </span>

                      <button
                        type="button"
                        onClick={() => {
                          setSelectedMovie(null);
                          setMovieSearch("");
                          setForm((current) => ({
                            ...current,
                            movie: "",
                          }));
                        }}
                      >
                        ×
                      </button>
                    </div>
                  )}
                </div>

                <label>
                  Cinemas

                  <button
                    type="button"
                    className="cinema-load-button"
                    onClick={() =>
                      loadCinemaCatalogue(
                        form.city,
                      )
                    }
                    disabled={
                      cinemaLoading ||
                      !form.city.trim()
                    }
                  >
                    {cinemaLoading
                      ? "Loading BookMyShow cinemas..."
                      : cinemaCatalogueCity ===
                          form.city.trim()
                        ? "Refresh cinemas"
                        : form.city.trim()
                          ? `Find cinemas in ${form.city.trim()}`
                          : "Enter a city first"}
                  </button>

                  {cinemaLoading && (
                    <div className="search-status">
                      Loading cinemas from BookMyShow...
                    </div>
                  )}

                  {cinemaCatalogueCity && (
                    <small className="cinema-catalogue-status">
                      Showing cinemas discovered on
                      BookMyShow for{" "}
                      <strong>
                        {cinemaCatalogueCity}
                      </strong>
                      .
                    </small>
                  )}

                  {cinemaError && (
                    <div className="cinema-search-error">
                      {cinemaError}
                    </div>
                  )}

                  {cinemaCatalogueCity && (
                    <div className="cinema-search-field">
                      <input
                        type="text"
                        value={cinemaSearch}
                        onChange={(event) =>
                          setCinemaSearch(
                            event.target.value,
                          )
                        }
                        placeholder={`Search cinemas in ${cinemaCatalogueCity}...`}
                        autoComplete="off"
                      />

                      {cinemaSearch.trim() && (
                        <div className="cinema-results">
                          {filteredCinemas.length > 0 ? (
                            filteredCinemas.map(
                              (cinema) => {
                                const selected =
                                  selectedCinemas.some(
                                    (item) =>
                                      item.provider_id ===
                                      cinema.provider_id,
                                  );

                                return (
                                  <button
                                    type="button"
                                    className={`cinema-result ${
                                      selected
                                        ? "selected"
                                        : ""
                                    }`}
                                    key={
                                      cinema.provider_id
                                    }
                                    onClick={() =>
                                      selectCinema(
                                        cinema,
                                      )
                                    }
                                  >
                                    <span>
                                      {cinema.name}
                                    </span>

                                    <small>
                                      {selected
                                        ? "Selected"
                                        : cinema.provider_id}
                                    </small>
                                  </button>
                                );
                              },
                            )
                          ) : (
                            <div className="cinema-no-results">
                              Requested theatre is not available
                              on BookMyShow in{" "}
                              <strong>
                                {cinemaCatalogueCity}
                              </strong>
                              .
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  )}

                  {selectedCinemas.length > 0 && (
                    <div className="selected-cinemas">
                      {selectedCinemas.map(
                        (cinema) => (
                          <div
                            className="selected-cinema"
                            key={cinema.provider_id}
                          >
                            <span>
                              {cinema.name}
                            </span>

                            <button
                              type="button"
                              onClick={() =>
                                setSelectedCinemas(
                                  (current) =>
                                    current.filter(
                                      (item) =>
                                        item.provider_id !==
                                        cinema.provider_id,
                                    ),
                                )
                              }
                              aria-label={`Remove ${cinema.name}`}
                            >
                              ×
                            </button>
                          </div>
                        ),
                      )}
                    </div>
                  )}

                  <small>
                    Search the BookMyShow catalogue and select
                    one or more exact cinema venues.
                  </small>
                </label>

                <button
                  className="new-watch-button form-submit-new"
                  type="submit"
                  disabled={creating}
                >
                  {creating
                    ? "Creating..."
                    : "Create watch"}
                </button>
              </form>
            </div>
          </div>
        )}
      </main>

      {currentSelectedWatch && (
        <div
          className="modal-overlay"
          onClick={() =>
            setSelectedWatch(null)
          }
        >
          <div
            className="watch-modal"
            onClick={(event) =>
              event.stopPropagation()
            }
          >
            <div className="modal-header">
              <div>
                <h2>
                  {currentSelectedWatch.movie}
                </h2>

                <p>
                  Watch details
                </p>
              </div>

              <button
                className="modal-close"
                onClick={() =>
                  setSelectedWatch(null)
                }
              >
                ×
              </button>
            </div>

            <div className="modal-details">
              <div>
                <span>City</span>
                <strong>
                  {currentSelectedWatch.city}
                </strong>
              </div>

              <div>
                <span>Target date</span>
                <strong>
                  {
                    currentSelectedWatch.target_date
                  }
                </strong>
              </div>

              <div>
                <span>Cinemas</span>
                <strong>
                  {currentSelectedWatch.cinemas.join(
                    ", ",
                  )}
                </strong>
              </div>

              <div>
                <span>Status</span>
                <strong>
                  {currentSelectedWatch.completed === true
                    ? "Monitoring stopped — tickets available"
                    : currentSelectedWatch.active
                      ? "Active"
                      : "Paused"}
                </strong>
              </div>
            </div>

            <section className="modal-section">
              <div className="modal-section-title">
                <h3>
                  Current availability
                </h3>

                <button
                  className="secondary-button"
                  onClick={() =>
                    refreshWatchDetails(
                      currentSelectedWatch.id,
                    )
                  }
                >
                  Refresh
                </button>
              </div>

              {renderModalAvailability(
                currentSelectedWatch,
              )}
            </section>

            <section className="modal-section">
              <div className="modal-section-title">
                <div>
                  <h3>
                    Detection history
                  </h3>

                  <p>
                    Availability changes
                    detected by the watcher.
                  </p>
                </div>
              </div>

              {renderHistory(
                currentSelectedWatch,
              )}
            </section>

            <div className="modal-footer">
              <button
                className="secondary-button"
                onClick={() =>
                  setSelectedWatch(null)
                }
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App; 
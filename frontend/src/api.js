const API_BASE_URL = "https://cinema-ticket-watcher.onrender.com";

async function request(endpoint, options = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    let message = `Request failed with status ${response.status}`;

    try {
      const data = await response.json();

      if (data.detail) {
        message = data.detail;
      }
    } catch {
      // Keep the default error message.
    }

    throw new Error(message);
  }

  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export async function getWatches() {
  return request("/watches");
}

export async function getWatch(watchId) {
  return request(`/watches/${watchId}`);
}

export async function getWatchStatus(watchId) {
  return request(`/watches/${watchId}/status`);
}

export async function getWatchHistory(watchId) {
  return request(`/watches/${watchId}/history`);
}

export async function getCinemas(city) {
  return request(`/cinemas/${encodeURIComponent(city)}`);
}

export async function getMovies(city, targetDate) {
  return request(
    `/movies/${encodeURIComponent(city)}/${encodeURIComponent(targetDate)}`,
  );
}

export async function createWatch(watch) {
  return request("/watches", {
    method: "POST",
    body: JSON.stringify(watch),
  });
}

export async function updateWatch(watchId, watch) {
  return request(`/watches/${watchId}`, {
    method: "PATCH",
    body: JSON.stringify(watch),
  });
}

export async function pauseWatch(watchId) {
  return request(`/watches/${watchId}/pause`, {
    method: "POST",
  });
}

export async function resumeWatch(watchId) {
  return request(`/watches/${watchId}/resume`, {
    method: "POST",
  });
}

export async function deleteWatch(watchId) {
  return request(`/watches/${watchId}`, {
    method: "DELETE",
  });
}

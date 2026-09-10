// Single API boundary for the whole frontend. Exports exactly the 9 contract
// operations from backend/openapi.yaml, backed by real fetch calls to the
// FastAPI backend (issue #12).
//
// Base URL comes from the VITE_API_BASE_URL env var so the backend host can be
// changed without touching code (e.g. set VITE_API_BASE_URL in a .env file).
// No other frontend file should reference the backend URL.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Non-2xx responses throw an Error with .status set, mirroring the previous
// mock's behavior so components need no changes. DELETE returns 204 with an
// empty body — don't crash parsing it.
async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!response.ok) {
    const error = new Error(`Request failed: ${response.status}`)
    error.status = response.status
    throw error
  }
  if (response.status === 204) return
  return response.json()
}

// --- GET /columns ---
export async function listColumns() {
  return request('/columns')
}

// --- POST /columns ---
export async function createColumn({ title }) {
  return request('/columns', {
    method: 'POST',
    body: JSON.stringify({ title }),
  })
}

// --- POST /columns/reorder ---
export async function reorderColumns({ column_ids }) {
  return request('/columns/reorder', {
    method: 'POST',
    body: JSON.stringify({ column_ids }),
  })
}

// --- PATCH /columns/{column_id} ---
export async function renameColumn(columnId, { title }) {
  return request(`/columns/${columnId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
}

// --- DELETE /columns/{column_id} --- (cascades to its cards)
export async function deleteColumn(columnId) {
  return request(`/columns/${columnId}`, { method: 'DELETE' })
}

// --- POST /columns/{column_id}/cards --- (new cards append)
export async function createCard(columnId, { title, notes = null, due_date = null }) {
  return request(`/columns/${columnId}/cards`, {
    method: 'POST',
    body: JSON.stringify({ title, notes, due_date }),
  })
}

// --- PATCH /cards/{card_id} --- (partial update; null clears)
export async function updateCard(cardId, fields) {
  return request(`/cards/${cardId}`, {
    method: 'PATCH',
    body: JSON.stringify(fields),
  })
}

// --- DELETE /cards/{card_id} ---
export async function deleteCard(cardId) {
  return request(`/cards/${cardId}`, { method: 'DELETE' })
}

// --- POST /cards/{card_id}/move ---
export async function moveCard(cardId, { column_id, position }) {
  return request(`/cards/${cardId}/move`, {
    method: 'POST',
    body: JSON.stringify({ column_id, position }),
  })
}

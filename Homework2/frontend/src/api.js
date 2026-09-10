// Single API boundary for the whole frontend. Exports exactly the 9 contract
// operations from backend/openapi.yaml. Currently mocked in-memory with the
// backend's #10 semantics; issue #12 swaps the bodies for fetch calls without
// touching components.

let nextColumnId = 1
let nextCardId = 1

// Default board per _docs/specs.md, seeded like the backend store.
const columns = [
  { id: nextColumnId++, title: 'To Do', position: 0, cards: [] },
  { id: nextColumnId++, title: 'Doing', position: 1, cards: [] },
  { id: nextColumnId++, title: 'Done', position: 2, cards: [] },
]

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function sortedColumns() {
  return [...columns].sort((a, b) => a.position - b.position)
}

function findColumn(id) {
  return columns.find((c) => c.id === id) || null
}

function findCard(id) {
  for (const column of columns) {
    const card = column.cards.find((card) => card.id === id)
    if (card) return card
  }
  return null
}

function notFound(what) {
  const error = new Error(`${what} not found`)
  error.status = 404
  throw error
}

function validation(message) {
  const error = new Error(message)
  error.status = 422
  throw error
}

// --- GET /columns ---
export async function listColumns() {
  return clone(sortedColumns())
}

// --- POST /columns ---
export async function createColumn({ title }) {
  const column = { id: nextColumnId++, title, position: columns.length, cards: [] }
  columns.push(column)
  return clone(column)
}

// --- POST /columns/reorder ---
export async function reorderColumns({ column_ids }) {
  const idSet = new Set(columns.map((c) => c.id))
  const given = new Set(column_ids)
  if (column_ids.length !== columns.length || column_ids.some((id) => !idSet.has(id))) {
    validation('column_ids must contain exactly the ids of all existing columns, once each')
  }
  if (given.size !== column_ids.length) {
    validation('column_ids must not contain duplicates')
  }
  column_ids.forEach((id, index) => {
    findColumn(id).position = index
  })
  return listColumns()
}

// --- PATCH /columns/{column_id} ---
export async function renameColumn(columnId, { title }) {
  const column = findColumn(columnId)
  if (!column) notFound('Column')
  column.title = title
  return clone(column)
}

// --- DELETE /columns/{column_id} --- (cascades to its cards)
export async function deleteColumn(columnId) {
  const index = columns.findIndex((c) => c.id === columnId)
  if (index === -1) notFound('Column')
  columns.splice(index, 1)
  columns.forEach((column, position) => {
    column.position = position
  })
}

// --- POST /columns/{column_id}/cards --- (new cards append)
export async function createCard(columnId, { title, notes = null, due_date = null }) {
  const column = findColumn(columnId)
  if (!column) notFound('Column')
  const card = {
    id: nextCardId++,
    column_id: column.id,
    title,
    notes,
    due_date,
  }
  column.cards.push(card)
  return clone(card)
}

// --- PATCH /cards/{card_id} --- (partial update; null clears)
export async function updateCard(cardId, fields) {
  const card = findCard(cardId)
  if (!card) notFound('Card')
  if ('title' in fields) card.title = fields.title
  if ('notes' in fields) card.notes = fields.notes
  if ('due_date' in fields) card.due_date = fields.due_date
  return clone(card)
}

// --- DELETE /cards/{card_id} ---
export async function deleteCard(cardId) {
  for (const column of columns) {
    const index = column.cards.findIndex((card) => card.id === cardId)
    if (index !== -1) {
      column.cards.splice(index, 1)
      return
    }
  }
  notFound('Card')
}

// --- POST /cards/{card_id}/move ---
// position is the 0-based index in the destination column AFTER the card is
// removed from its old spot; positions beyond the end clamp to the end.
export async function moveCard(cardId, { column_id, position }) {
  if (position < 0) validation('position must be >= 0')
  const card = findCard(cardId)
  if (!card) notFound('Card')
  const destination = findColumn(column_id)
  if (!destination) notFound('Column')

  const origin = findColumn(card.column_id)
  origin.cards.splice(origin.cards.indexOf(card), 1)
  const index = Math.min(position, destination.cards.length)
  card.column_id = destination.id
  destination.cards.splice(index, 0, card)
  return clone(card)
}

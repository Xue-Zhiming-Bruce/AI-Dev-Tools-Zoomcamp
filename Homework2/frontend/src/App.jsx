import { useEffect, useState } from 'react'
import * as api from './api.js'
import Column from './Column.jsx'
import CardDialog from './CardDialog.jsx'

export default function App() {
  const [columns, setColumns] = useState([])
  // cardDialog: { mode: 'create', columnId } | { mode: 'edit', card } | null
  const [cardDialog, setCardDialog] = useState(null)
  // columnDrag: id of the column being dragged
  const [columnDragId, setColumnDragId] = useState(null)
  // columnDropIndex: where a dragged column would land
  const [columnDropIndex, setColumnDropIndex] = useState(null)

  useEffect(() => {
    api.listColumns().then(setColumns)
  }, [])

  async function refresh() {
    setColumns(await api.listColumns())
  }

  async function handleAddColumn() {
    const title = window.prompt('Column name')
    if (!title) return
    await api.createColumn({ title })
    await refresh()
  }

  async function handleRenameColumn(columnId, title) {
    if (!title) return
    await api.renameColumn(columnId, { title })
    await refresh()
  }

  async function handleDeleteColumn(columnId) {
    if (!window.confirm('Delete this column and all its cards?')) return
    await api.deleteColumn(columnId)
    await refresh()
  }

  async function handleColumnDrop(targetIndex) {
    const from = columns.findIndex((c) => c.id === columnDragId)
    setColumnDragId(null)
    setColumnDropIndex(null)
    if (from === -1 || targetIndex === null || from === targetIndex) return
    const ids = columns.map((c) => c.id)
    ids.splice(from, 1)
    ids.splice(targetIndex, 0, columnDragId)
    setColumns(await api.reorderColumns({ column_ids: ids }))
  }

  function handleHeaderDragOver(event, index) {
    if (!columnDragId) return
    event.preventDefault()
    event.stopPropagation()
    const rect = event.currentTarget.getBoundingClientRect()
    const after = event.clientX > rect.left + rect.width / 2
    const dropIndex = index + (after ? 1 : 0)
    // dragging over its own old spot is a no-op
    if (dropIndex === columnDragIndex(columns, columnDragId) || dropIndex === columnDragIndex(columns, columnDragId) + 1) {
      setColumnDropIndex(null)
      return
    }
    setColumnDropIndex(dropIndex)
  }

  async function handleCardDrop(cardId, targetColumnId, targetIndex) {
    await api.moveCard(cardId, { column_id: targetColumnId, position: targetIndex })
    await refresh()
  }

  async function handleSaveCard(dialogState, fields) {
    if (dialogState.mode === 'create') {
      await api.createCard(dialogState.columnId, fields)
    } else {
      await api.updateCard(dialogState.card.id, fields)
    }
    setCardDialog(null)
    await refresh()
  }

  async function handleDeleteCard(card) {
    if (!window.confirm(`Delete card "${card.title}"?`)) return
    await api.deleteCard(card.id)
    await refresh()
  }

  return (
    <main className="board-wrap">
      <h1>MyKanban</h1>
      <div
        className="board"
        onDragOver={(event) => columnDragId && event.preventDefault()}
        onDrop={(event) => {
          if (columnDragId) {
            event.preventDefault()
            handleColumnDrop(columnDropIndex ?? columns.length)
          }
        }}
      >
        {columns.map((column, index) => (
          <Column
            key={column.id}
            column={column}
            isColumnDragged={column.id === columnDragId}
            showColumnDropBefore={columnDropIndex === index}
            onHeaderDragStart={() => setColumnDragId(column.id)}
            onHeaderDragEnd={() => {
              setColumnDragId(null)
              setColumnDropIndex(null)
            }}
            onHeaderDragOver={(event) => handleHeaderDragOver(event, index)}
            onRename={(title) => handleRenameColumn(column.id, title)}
            onDelete={() => handleDeleteColumn(column.id)}
            onAddCard={() => setCardDialog({ mode: 'create', columnId: column.id })}
            onEditCard={(card) => setCardDialog({ mode: 'edit', card })}
            onDeleteCard={handleDeleteCard}
            onCardDrop={handleCardDrop}
          />
        ))}
        {columnDragId && columnDropIndex === columns.length && <div className="column-drop-edge" />}
        <button className="add-column" onClick={handleAddColumn}>
          + Add column
        </button>
      </div>
      {cardDialog && (
        <CardDialog
          card={cardDialog.mode === 'edit' ? cardDialog.card : null}
          onSave={(fields) => handleSaveCard(cardDialog, fields)}
          onClose={() => setCardDialog(null)}
        />
      )}
    </main>
  )
}

function columnDragIndex(columns, columnId) {
  return columns.findIndex((c) => c.id === columnId)
}

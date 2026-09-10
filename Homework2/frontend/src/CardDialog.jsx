import { useRef, useState } from 'react'

// Native <dialog> for both creating and editing a card.
export default function CardDialog({ card, onSave, onClose }) {
  const [title, setTitle] = useState(card?.title ?? '')
  const [notes, setNotes] = useState(card?.notes ?? '')
  const [dueDate, setDueDate] = useState(card?.due_date ?? '')
  const dialogRef = useRef(null)
  if (dialogRef.current && !dialogRef.current.open) dialogRef.current.showModal()

  function handleSubmit(event) {
    event.preventDefault()
    if (!title.trim()) return
    onSave({
      title: title.trim(),
      notes: notes.trim() || null,
      due_date: dueDate || null,
    })
  }

  return (
    <dialog
      ref={dialogRef}
      className="card-dialog"
      onClose={onClose}
      onClick={(event) => {
        if (event.target === dialogRef.current) onClose()
      }}
    >
      <form onSubmit={handleSubmit}>
        <h2>{card ? 'Edit card' : 'New card'}</h2>
        <label>
          Title
          <input
            value={title}
            required
            autoFocus
            onChange={(event) => setTitle(event.target.value)}
          />
        </label>
        <label>
          Notes
          <textarea
            value={notes ?? ''}
            rows={4}
            onChange={(event) => setNotes(event.target.value)}
          />
        </label>
        <label>
          Due date
          <input
            type="date"
            value={dueDate ?? ''}
            onChange={(event) => setDueDate(event.target.value)}
          />
        </label>
        <menu className="dialog-actions">
          <button type="button" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="primary">
            Save
          </button>
        </menu>
      </form>
    </dialog>
  )
}

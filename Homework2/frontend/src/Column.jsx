import { useState } from 'react'

export default function Column({
  column,
  isColumnDragged,
  showColumnDropBefore,
  onHeaderDragStart,
  onHeaderDragEnd,
  onHeaderDragOver,
  onRename,
  onDelete,
  onAddCard,
  onEditCard,
  onDeleteCard,
  onCardDrop,
}) {
  const [renaming, setRenaming] = useState(false)
  const [draftTitle, setDraftTitle] = useState(column.title)
  // drop: { index } insertion point for a dragged card within this column
  const [cardDropIndex, setCardDropIndex] = useState(null)

  function startRename() {
    setDraftTitle(column.title)
    setRenaming(true)
  }

  function commitRename() {
    setRenaming(false)
    if (draftTitle !== column.title) onRename(draftTitle.trim() || column.title)
  }

  function cardDragOver(event) {
    if (event.dataTransfer.types.includes('text/column')) return
    event.preventDefault()
    const cards = column.cards
    let index = cards.length
    for (let i = 0; i < cards.length; i++) {
      const rect = event.currentTarget.closest('.card-slot')?.getBoundingClientRect()
      if (!rect) break
      if (event.clientY < rect.top + rect.height / 2) {
        index = i
        break
      }
    }
    setCardDropIndex(index)
  }

  function cardDrop(event, computedIndex) {
    event.preventDefault()
    const cardId = Number(event.dataTransfer.getData('text/card'))
    setCardDropIndex(null)
    if (!cardId) return
    // Backend position is the index among the destination cards excluding the
    // dragged card itself (it is removed first). Same column + moving down
    // means the visual index overcounts by one.
    const from = column.cards.findIndex((card) => card.id === cardId)
    let position = computedIndex
    if (from !== -1 && from < position) position -= 1
    onCardDrop(cardId, column.id, position)
  }

  return (
    <section
      className={`column${isColumnDragged ? ' column-dragged' : ''}`}
      data-column-id={column.id}
    >
      {showColumnDropBefore && <div className="column-drop-marker" />}
      <header
        className="column-header"
        draggable
        onDragStart={(event) => {
          event.dataTransfer.setData('text/column', String(column.id))
          event.dataTransfer.effectAllowed = 'move'
          onHeaderDragStart()
        }}
        onDragEnd={onHeaderDragEnd}
        onDragOver={onHeaderDragOver}
      >
        {renaming ? (
          <input
            className="column-title-input"
            value={draftTitle}
            autoFocus
            onChange={(event) => setDraftTitle(event.target.value)}
            onBlur={commitRename}
            onKeyDown={(event) => {
              if (event.key === 'Enter') commitRename()
              if (event.key === 'Escape') setRenaming(false)
            }}
          />
        ) : (
          <h2 onClick={startRename} title="Click to rename">
            {column.title}
          </h2>
        )}
        <span className="column-actions">
          <button className="icon-btn" onClick={onDelete} title="Delete column">
            ✕
          </button>
        </span>
      </header>
      <div
        className="column-body"
        onDragOver={cardDragOver}
        onDrop={(event) => cardDrop(event, cardDropIndex ?? column.cards.length)}
        onDragLeave={(event) => {
          if (!event.currentTarget.contains(event.relatedTarget)) setCardDropIndex(null)
        }}
      >
        {column.cards.map((card, index) => (
          <div key={card.id}>
            {cardDropIndex === index && <div className="card-placeholder" />}
            <article
              className="card"
              draggable
              onDragStart={(event) => {
                event.dataTransfer.setData('text/card', String(card.id))
                event.dataTransfer.effectAllowed = 'move'
              }}
              onClick={() => onEditCard(card)}
            >
              <h3>{card.title}</h3>
              {card.notes && <p className="card-notes">{card.notes}</p>}
              {card.due_date && <span className="card-due">📅 {card.due_date}</span>}
            </article>
          </div>
        ))}
        {cardDropIndex === column.cards.length && <div className="card-placeholder" />}
      </div>
      <button className="add-card" onClick={onAddCard}>
        + Add card
      </button>
    </section>
  )
}

from fastapi import FastAPI

app = FastAPI(
    title="MyKanban API",
    description="Backend for the MyKanban personal Kanban board. "
    "The committed openapi.yaml is the reviewed contract (issue #9).",
    version="0.1.0",
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}

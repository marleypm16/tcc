"""Aplicação FastAPI (processo 1)."""

from fastapi import FastAPI


def criar_app() -> FastAPI:
    app = FastAPI(title="Lastro")

    @app.get("/saude")
    def saude() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = criar_app()

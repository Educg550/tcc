from fastapi.responses import FileResponse


def registra_rota_padrao(app, base_dir):
    @app.get("/")
    def index():
        return FileResponse(str(base_dir / "index.html"))

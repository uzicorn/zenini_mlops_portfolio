from fastapi import FastAPI, Path
from fastapi.responses import HTMLResponse
from .utils import get_backend_data

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Webapp is running"}


@app.get("/backend/{query}", response_class=HTMLResponse)
async def show_backend_data(query: str = Path(..., description="Query values: runs, data_sources, artifacts")):
    return get_backend_data(query)


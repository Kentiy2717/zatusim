from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title='Zatusim API',
    description='Социальный лаунчер для живых тусовок и игр',
    version='0.1.0',
)

# Подключение статики и шаблонов
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')


@app.get('/healthcheck', tags=['Health'])
async def healthcheck() -> dict[str, str]:
    return {'status': 'ok', 'project': 'Zatusim'}


@app.get('/', response_class=HTMLResponse, tags=['Frontend'])
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'title': 'Zatusim — Тусовки и Игры'},
    )

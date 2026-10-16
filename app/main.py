from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title=f'{settings.PROJECT_NAME} API',
    description='Социальный лаунчер для живых тусовок и игр',
    version='0.1.0',
)

# Подключение статики и шаблонов
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')

# Подключение API роутеров модулей
app.include_router(users_router, prefix='/api/v1/users', tags=['Users'])
app.include_router(auth_router, prefix='/api/v1/auth', tags=['auth'])


@app.get('/healthcheck', tags=['Health'])
async def healthcheck() -> dict[str, str]:
    """Эндпоинт проверки работоспособности сервиса."""
    return {'status': 'ok', 'project_name': settings.PROJECT_NAME}


@app.get('/', response_class=HTMLResponse, tags=['Frontend'])
async def index(request: Request) -> HTMLResponse:
    """Главная страница сайта (SSR Jinja2)."""

    return templates.TemplateResponse(
        request=request,
        name='index.html',
        context={'project_name': settings.PROJECT_NAME},
    )

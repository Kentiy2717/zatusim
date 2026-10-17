from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import settings
from app.modules.auth.router import router as auth_router
from app.modules.users.router import router as users_router

BASE_DIR = Path(__file__).resolve().parent

# Создаем папку для загрузок, если ее нет.
uploads_dir = Path('uploads')
uploads_dir.mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=f'{settings.PROJECT_NAME} API',
    description='Социальный лаунчер для живых тусовок и игр',
    version='0.1.0',
)

# Настройка CORS (Cross-Origin Resource Sharing)
# Разрешаем фронтенду (React Native/Web) обращаться к нашему API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=['*'],  # Разрешаем все методы (GET, POST, OPTIONS, PUT, DELETE)
    allow_headers=['*'],  # Разрешаем все заголовки (включая Authorization: Bearer)
)

# Подключение статики и шаблонов
app.mount('/uploads', StaticFiles(directory='uploads'), name='uploads')
app.mount('/static', StaticFiles(directory=BASE_DIR / 'static'), name='static')
templates = Jinja2Templates(directory=BASE_DIR / 'templates')

# Подключение API роутеров модулей
app.include_router(users_router, prefix='/api/v1')
app.include_router(auth_router, prefix='/api/v1')


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

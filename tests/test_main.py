from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthcheck() -> None:
    """Проверка JSON-эндпоинта статуса системы."""
    response = client.get('/healthcheck')
    assert response.status_code == 200
    assert response.json() == {'status': 'ok', 'project': 'Zatusim'}


def test_index_page() -> None:
    """Проверка рендеринга главной HTML-страницы."""
    response = client.get('/')
    assert response.status_code == 200
    assert 'Затусим?' in response.text
    assert 'text/html' in response.headers['content-type']

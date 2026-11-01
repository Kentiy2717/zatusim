from httpx import AsyncClient


async def test_healthcheck(client: AsyncClient) -> None:
    """Тест эндпоинта /healthcheck."""

    response = await client.get('/healthcheck')
    assert response.status_code == 200
    data = response.json()
    assert data['status'] == 'ok'


async def test_index_page(client: AsyncClient) -> None:
    """Проверка рендеринга главной HTML-страницы."""

    response = await client.get('/')
    assert response.status_code == 200
    assert 'Затусим?' in response.text
    assert 'text/html' in response.headers['content-type']

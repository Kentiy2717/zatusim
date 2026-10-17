from fastapi.testclient import TestClient

from tests.test_users import delete_user_by_email


def test_login_success(client: TestClient) -> None:
    """Тест успешного входа и получения JWT-токена."""

    user_data = {
        'email': 'auth_user@example.com',
        'password': 'password123',
        'first_name': 'Петр',
        'gender': 'M',
        'preference': 'F',
    }

    try:
        # 1. Регистрируем пользователя
        reg_resp = client.post('/api/v1/users/register', json=user_data)
        assert reg_resp.status_code == 201

        # 2. Выполняем вход
        login_data = {
            'email': user_data['email'],
            'password': user_data['password'],
        }
        login_resp = client.post('/api/v1/auth/login', json=login_data)
        assert login_resp.status_code == 200

        data = login_resp.json()
        assert 'access_token' in data
        assert data['token_type'] == 'bearer'
    finally:
        delete_user_by_email(user_data['email'])


def test_login_invalid_credentials(client: TestClient) -> None:
    """Тест ошибки входа при неверном пароле."""

    user_data = {
        'email': 'auth_wrong_pwd@example.com',
        'password': 'correct_password',
        'first_name': 'Петр',
        'gender': 'M',
        'preference': 'F',
    }

    try:
        client.post('/api/v1/users/register', json=user_data)

        # Пробуем войти с неверным паролем
        login_data = {
            'email': user_data['email'],
            'password': 'WRONG_password',
        }
        response = client.post('/api/v1/auth/login', json=login_data)
        assert response.status_code == 401
        assert response.json()['detail'] == 'Неверный email или пароль.'
    finally:
        delete_user_by_email(user_data['email'])


def test_get_me_success(client: TestClient) -> None:
    """Тест получения профиля авторизованного пользователя через /me."""

    user_data = {
        'email': 'get_me_user@example.com',
        'password': 'password123',
        'first_name': 'Алексей',
        'gender': 'M',
        'preference': 'F',
    }

    try:
        # 1. Регистрируем
        client.post('/api/v1/users/register', json=user_data)

        # 2. Логинимся и забираем токен
        login_resp = client.post(
            '/api/v1/auth/login',
            json={'email': user_data['email'], 'password': user_data['password']},
        )
        token = login_resp.json()['access_token']

        # 3. Делаем запрос к /me с заголовком Authorization: Bearer <token>
        headers = {'Authorization': f'Bearer {token}'}
        me_resp = client.get('/api/v1/users/me', headers=headers)

        assert me_resp.status_code == 200
        data = me_resp.json()
        assert data['email'] == user_data['email']
        assert data['first_name'] == user_data['first_name']
    finally:
        delete_user_by_email(user_data['email'])


def test_get_me_unauthorized(client: TestClient) -> None:
    """Тест доступа к /me без токена (должен вернуть 401)."""

    response = client.get('/api/v1/users/me')
    assert response.status_code == 401

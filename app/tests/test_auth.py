"""Auth endpoint tests (register / login)."""


class TestHealth:
    def test_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200


class TestRegister:
    def test_success(self, client):
        res = client.post("/auth/register", json={"email": "new@example.com", "password": "pass123"})
        assert res.status_code == 201
        body = res.json()
        assert body["email"] == "new@example.com"
        assert "id" in body

    def test_duplicate_email_returns_400(self, client):
        client.post("/auth/register", json={"email": "dup@example.com", "password": "pass"})
        res = client.post("/auth/register", json={"email": "dup@example.com", "password": "pass"})
        assert res.status_code == 400

    def test_invalid_email_returns_422(self, client):
        res = client.post("/auth/register", json={"email": "not-an-email", "password": "pass"})
        assert res.status_code == 422


class TestLogin:
    def test_success_returns_token(self, client):
        client.post("/auth/register", json={"email": "user@example.com", "password": "pass123"})
        res = client.post("/auth/login", data={"username": "user@example.com", "password": "pass123"})
        assert res.status_code == 200
        body = res.json()
        assert "access_token" in body
        assert body["token_type"] == "bearer"

    def test_wrong_password_returns_401(self, client):
        client.post("/auth/register", json={"email": "user@example.com", "password": "pass123"})
        res = client.post("/auth/login", data={"username": "user@example.com", "password": "wrong"})
        assert res.status_code == 401

    def test_unknown_user_returns_401(self, client):
        res = client.post("/auth/login", data={"username": "nobody@example.com", "password": "pass"})
        assert res.status_code == 401

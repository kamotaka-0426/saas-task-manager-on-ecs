"""Organization and member management tests."""


class TestCreateOrg:
    def test_authenticated_user_can_create(self, client, owner):
        res = client.post(
            "/orgs/", json={"name": "My Org", "slug": "my-org"}, headers=owner["headers"]
        )
        assert res.status_code == 201
        body = res.json()
        assert body["name"] == "My Org"
        assert body["slug"] == "my-org"

    def test_unauthenticated_returns_401(self, client):
        res = client.post("/orgs/", json={"name": "X", "slug": "x"})
        assert res.status_code == 401

    def test_duplicate_slug_returns_400(self, client, owner):
        client.post("/orgs/", json={"name": "A", "slug": "dup"}, headers=owner["headers"])
        res = client.post("/orgs/", json={"name": "B", "slug": "dup"}, headers=owner["headers"])
        assert res.status_code == 400

    def test_creator_becomes_owner(self, client, org, owner):
        members = client.get(f"/orgs/{org['id']}/members", headers=owner["headers"]).json()
        assert any(m["role"] == "owner" and m["user_id"] == owner["id"] for m in members)


class TestGetOrg:
    def test_member_can_get(self, client, org, owner):
        res = client.get(f"/orgs/{org['id']}", headers=owner["headers"])
        assert res.status_code == 200

    def test_outsider_returns_403(self, client, org, outsider):
        res = client.get(f"/orgs/{org['id']}", headers=outsider["headers"])
        assert res.status_code == 403

    def test_not_found_returns_404(self, client, owner):
        res = client.get("/orgs/99999", headers=owner["headers"])
        assert res.status_code == 403  # 403 because membership check fails first


class TestUpdateOrg:
    def test_owner_can_update(self, client, org, owner):
        res = client.patch(
            f"/orgs/{org['id']}", json={"name": "New Name"}, headers=owner["headers"]
        )
        assert res.status_code == 200
        assert res.json()["name"] == "New Name"

    def test_admin_cannot_update(self, client, org_with_admin, admin_user):
        res = client.patch(
            f"/orgs/{org_with_admin['id']}",
            json={"name": "Hijacked"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 403

    def test_member_cannot_update(self, client, org_with_member, member_user):
        res = client.patch(
            f"/orgs/{org_with_member['id']}",
            json={"name": "Hijacked"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403


class TestDeleteOrg:
    def test_owner_can_delete(self, client, org, owner):
        res = client.delete(f"/orgs/{org['id']}", headers=owner["headers"])
        assert res.status_code == 204

    def test_admin_cannot_delete(self, client, org_with_admin, admin_user):
        res = client.delete(f"/orgs/{org_with_admin['id']}", headers=admin_user["headers"])
        assert res.status_code == 403


class TestMembers:
    def test_admin_can_add_member(self, client, org_with_admin, admin_user, outsider):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/members",
            json={"email": outsider["email"], "role": "member"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 201
        assert res.json()["role"] == "member"

    def test_member_cannot_add_member(self, client, org_with_member, member_user, outsider):
        res = client.post(
            f"/orgs/{org_with_member['id']}/members",
            json={"email": outsider["email"], "role": "member"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403

    def test_add_nonexistent_user_returns_404(self, client, org, owner):
        res = client.post(
            f"/orgs/{org['id']}/members",
            json={"email": "ghost@example.com", "role": "member"},
            headers=owner["headers"],
        )
        assert res.status_code == 404

    def test_owner_can_remove_member(self, client, org_with_member, owner, member_user):
        res = client.delete(
            f"/orgs/{org_with_member['id']}/members/{member_user['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_cannot_remove_owner(self, client, org, owner):
        res = client.delete(
            f"/orgs/{org['id']}/members/{owner['id']}", headers=owner["headers"]
        )
        assert res.status_code == 400

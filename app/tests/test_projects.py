"""Project CRUD and RBAC tests."""


class TestCreateProject:
    def test_admin_can_create(self, client, org_with_admin, admin_user):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/",
            json={"name": "Beta", "description": "Second project"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 201
        assert res.json()["name"] == "Beta"

    def test_member_cannot_create(self, client, org_with_member, member_user):
        res = client.post(
            f"/orgs/{org_with_member['id']}/projects/",
            json={"name": "Beta"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403

    def test_outsider_cannot_create(self, client, org, outsider):
        res = client.post(
            f"/orgs/{org['id']}/projects/",
            json={"name": "Beta"},
            headers=outsider["headers"],
        )
        assert res.status_code == 403

    def test_unauthenticated_returns_401(self, client, org):
        res = client.post(f"/orgs/{org['id']}/projects/", json={"name": "Beta"})
        assert res.status_code == 401


class TestListProjects:
    def test_member_can_list(self, client, project, org_with_member, member_user):
        res = client.get(
            f"/orgs/{org_with_member['id']}/projects/", headers=member_user["headers"]
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_outsider_cannot_list(self, client, project, org_with_admin, outsider):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/", headers=outsider["headers"]
        )
        assert res.status_code == 403


class TestGetProject:
    def test_member_can_get(self, client, project, org_with_member, member_user):
        res = client.get(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}",
            headers=member_user["headers"],
        )
        assert res.status_code == 200

    def test_wrong_org_returns_404(self, client, project, owner):
        res = client.post("/orgs/", json={"name": "Other", "slug": "other"}, headers=owner["headers"])
        other_org_id = res.json()["id"]
        res = client.get(
            f"/orgs/{other_org_id}/projects/{project['id']}", headers=owner["headers"]
        )
        assert res.status_code == 404


class TestUpdateProject:
    def test_admin_can_update(self, client, project, org_with_admin, admin_user):
        res = client.patch(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}",
            json={"name": "Alpha v2"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 200
        assert res.json()["name"] == "Alpha v2"

    def test_member_cannot_update(self, client, project, org_with_member, member_user):
        res = client.patch(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}",
            json={"name": "Hijacked"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403


class TestDeleteProject:
    def test_owner_can_delete(self, client, project, org_with_admin, owner):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_admin_cannot_delete(self, client, project, org_with_admin, admin_user):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}",
            headers=admin_user["headers"],
        )
        assert res.status_code == 403

    def test_nonexistent_returns_404(self, client, org, owner):
        res = client.delete(f"/orgs/{org['id']}/projects/99999", headers=owner["headers"])
        assert res.status_code == 404

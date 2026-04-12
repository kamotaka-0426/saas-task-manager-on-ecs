"""Issue CRUD and RBAC tests."""


class TestCreateIssue:
    def test_admin_can_create(self, client, project, org_with_admin, admin_user):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/",
            json={"title": "Fix bug", "priority": "high"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 201
        body = res.json()
        assert body["title"] == "Fix bug"
        assert body["priority"] == "high"
        assert body["status"] == "backlog"

    def test_member_cannot_create(self, client, project, org_with_member, member_user):
        res = client.post(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/",
            json={"title": "Fix bug"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403

    def test_outsider_cannot_create(self, client, project, org_with_admin, outsider):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/",
            json={"title": "Fix bug"},
            headers=outsider["headers"],
        )
        assert res.status_code == 403


class TestListIssues:
    def test_member_can_list(self, client, issue, project, org_with_member, member_user):
        res = client.get(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/",
            headers=member_user["headers"],
        )
        assert res.status_code == 200
        assert len(res.json()["items"]) == 1

    def test_outsider_cannot_list(self, client, issue, project, org_with_admin, outsider):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/",
            headers=outsider["headers"],
        )
        assert res.status_code == 403


class TestGetIssue:
    def test_member_can_get(self, client, issue, project, org_with_member, member_user):
        res = client.get(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/{issue['id']}",
            headers=member_user["headers"],
        )
        assert res.status_code == 200

    def test_nonexistent_returns_404(self, client, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/99999",
            headers=owner["headers"],
        )
        assert res.status_code == 404


class TestUpdateIssue:
    def test_admin_can_update_status(self, client, issue, project, org_with_admin, admin_user):
        res = client.patch(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}",
            json={"status": "in_progress"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 200
        assert res.json()["status"] == "in_progress"

    def test_member_cannot_update(self, client, issue, project, org_with_member, member_user):
        res = client.patch(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/{issue['id']}",
            json={"title": "Hijacked"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403

    def test_invalid_status_returns_422(self, client, issue, project, org_with_admin, owner):
        res = client.patch(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}",
            json={"status": "flying"},
            headers=owner["headers"],
        )
        assert res.status_code == 422


class TestDeleteIssue:
    def test_owner_can_delete(self, client, issue, project, org_with_admin, owner):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_admin_cannot_delete(self, client, issue, project, org_with_admin, admin_user):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}",
            headers=admin_user["headers"],
        )
        assert res.status_code == 403

    def test_nonexistent_returns_404(self, client, project, org_with_admin, owner):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/99999",
            headers=owner["headers"],
        )
        assert res.status_code == 404

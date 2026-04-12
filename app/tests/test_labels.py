"""Label CRUD and issue label/assignee tests."""
import pytest


@pytest.fixture
def label(client, org_with_admin, owner):
    res = client.post(
        f"/orgs/{org_with_admin['id']}/labels/",
        json={"name": "bug", "color": "#ef4444"},
        headers=owner["headers"],
    )
    assert res.status_code == 201
    return res.json()


class TestLabels:
    def test_admin_can_create_label(self, client, org_with_admin, admin_user):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/labels/",
            json={"name": "feature", "color": "#6366f1"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 201
        assert res.json()["name"] == "feature"

    def test_member_cannot_create_label(self, client, org_with_member, member_user):
        res = client.post(
            f"/orgs/{org_with_member['id']}/labels/",
            json={"name": "bug", "color": "#ff0000"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403

    def test_duplicate_name_returns_400(self, client, label, org_with_admin, owner):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/labels/",
            json={"name": "bug", "color": "#000000"},
            headers=owner["headers"],
        )
        assert res.status_code == 400

    def test_invalid_color_returns_422(self, client, org_with_admin, owner):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/labels/",
            json={"name": "x", "color": "red"},
            headers=owner["headers"],
        )
        assert res.status_code == 422

    def test_member_can_list_labels(self, client, label, org_with_member, member_user):
        res = client.get(
            f"/orgs/{org_with_member['id']}/labels/",
            headers=member_user["headers"],
        )
        assert res.status_code == 200
        assert len(res.json()) == 1

    def test_owner_can_delete_label(self, client, label, org_with_admin, owner):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/labels/{label['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_admin_cannot_delete_label(self, client, label, org_with_admin, admin_user):
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/labels/{label['id']}",
            headers=admin_user["headers"],
        )
        assert res.status_code == 403


class TestIssueLabelAssignment:
    def test_add_label_to_issue(self, client, issue, project, label, org_with_admin, owner):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/labels/{label['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 201
        assert any(lb["id"] == label["id"] for lb in res.json()["labels"])

    def test_add_duplicate_label_returns_400(self, client, issue, project, label, org_with_admin, owner):
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/labels/{label['id']}",
            headers=owner["headers"],
        )
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/labels/{label['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 400

    def test_remove_label_from_issue(self, client, issue, project, label, org_with_admin, owner):
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/labels/{label['id']}",
            headers=owner["headers"],
        )
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/labels/{label['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_member_cannot_add_label(self, client, issue, project, label, org_with_member, member_user):
        res = client.post(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/{issue['id']}/labels/{label['id']}",
            headers=member_user["headers"],
        )
        assert res.status_code == 403


class TestIssueAssignees:
    def test_admin_can_assign(self, client, issue, project, org_with_admin, owner, admin_user):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 201
        assert any(a["id"] == admin_user["id"] for a in res.json()["assignees"])

    def test_add_duplicate_assignee_returns_400(self, client, issue, project, org_with_admin, owner, admin_user):
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 400

    def test_admin_can_unassign(self, client, issue, project, org_with_admin, owner, admin_user):
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_assignee_log_recorded(self, client, issue, project, org_with_admin, owner, admin_user):
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/activity",
            headers=owner["headers"],
        )
        logs = res.json()
        assert any(log["action"] == "assigned" for log in logs)

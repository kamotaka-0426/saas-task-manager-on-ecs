"""Comment CRUD and RBAC tests."""


class TestCreateComment:
    def test_admin_can_comment(self, client, issue, project, org_with_admin, admin_user):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "Looks good to me!"},
            headers=admin_user["headers"],
        )
        assert res.status_code == 201
        body = res.json()
        assert body["content"] == "Looks good to me!"
        assert body["issue_id"] == issue["id"]

    def test_member_cannot_comment(self, client, issue, project, org_with_member, member_user):
        res = client.post(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "Hello"},
            headers=member_user["headers"],
        )
        assert res.status_code == 403

    def test_outsider_cannot_comment(self, client, issue, project, org_with_admin, outsider):
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "Hello"},
            headers=outsider["headers"],
        )
        assert res.status_code == 403


class TestListComments:
    def test_member_can_list(self, client, issue, project, org_with_member, member_user, owner):
        # admin adds comment first
        client.post(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "First comment"},
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_member['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            headers=member_user["headers"],
        )
        assert res.status_code == 200
        assert len(res.json()) == 1


class TestDeleteComment:
    def test_author_can_delete_own_comment(self, client, issue, project, org_with_admin, owner):
        create_res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "To delete"},
            headers=owner["headers"],
        )
        comment_id = create_res.json()["id"]
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments/{comment_id}",
            headers=owner["headers"],
        )
        assert res.status_code == 204

    def test_cannot_delete_others_comment(self, client, issue, project, org_with_admin, owner, admin_user):
        create_res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "Owner's comment"},
            headers=owner["headers"],
        )
        comment_id = create_res.json()["id"]
        res = client.delete(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments/{comment_id}",
            headers=admin_user["headers"],
        )
        assert res.status_code == 403


class TestActivityLog:
    def test_create_issue_logs_activity(self, client, issue, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/activity",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        logs = res.json()
        assert any(log["action"] == "created" for log in logs)

    def test_update_status_logs_activity(self, client, issue, project, org_with_admin, owner):
        client.patch(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}",
            json={"status": "in_progress"},
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/activity",
            headers=owner["headers"],
        )
        logs = res.json()
        status_log = next((l for l in logs if l["action"] == "status_changed"), None)
        assert status_log is not None
        assert status_log["old_value"] == "backlog"
        assert status_log["new_value"] == "in_progress"

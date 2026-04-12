"""Issue filter, sort, and cursor pagination tests."""
import pytest


@pytest.fixture
def three_issues(client, project, org_with_admin, owner):
    """Create 3 issues with different status/priority."""
    issues = []
    specs = [
        {"title": "Alpha", "status": "todo",        "priority": "high"},
        {"title": "Beta",  "status": "in_progress", "priority": "low"},
        {"title": "Gamma", "status": "backlog",      "priority": "urgent"},
    ]
    for spec in specs:
        res = client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/",
            json=spec,
            headers=owner["headers"],
        )
        assert res.status_code == 201
        issues.append(res.json())
    return issues


class TestIssueFilters:
    def test_filter_by_status(self, client, three_issues, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?status=todo",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "Alpha"

    def test_filter_by_priority(self, client, three_issues, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?priority=urgent",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        assert res.json()["total"] == 1
        assert res.json()["items"][0]["title"] == "Gamma"

    def test_filter_by_assignee(self, client, three_issues, project, org_with_admin, owner, admin_user):
        # assign admin_user to Alpha
        issue_id = three_issues[0]["id"]
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue_id}/assignees/{admin_user['id']}",
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?assignee_id={admin_user['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        assert res.json()["total"] == 1

    def test_filter_by_label(self, client, three_issues, project, org_with_admin, owner):
        # create a label and attach to Beta
        label = client.post(
            f"/orgs/{org_with_admin['id']}/labels/",
            json={"name": "backend", "color": "#6366f1"},
            headers=owner["headers"],
        ).json()
        issue_id = three_issues[1]["id"]
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue_id}/labels/{label['id']}",
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?label_id={label['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        assert res.json()["total"] == 1

    def test_invalid_sort_returns_422(self, client, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?sort=invalid",
            headers=owner["headers"],
        )
        assert res.status_code == 422

    def test_pagination_limit(self, client, three_issues, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?limit=2",
            headers=owner["headers"],
        )
        body = res.json()
        assert len(body["items"]) == 2
        assert body["total"] == 3
        assert body["next_cursor"] is not None

    def test_cursor_pagination(self, client, three_issues, project, org_with_admin, owner):
        # Get first page (1 item)
        page1 = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?limit=2",
            headers=owner["headers"],
        ).json()
        assert len(page1["items"]) == 2
        cursor = page1["next_cursor"]
        assert cursor is not None

        # Get second page using cursor
        page2 = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?limit=2&cursor={cursor}",
            headers=owner["headers"],
        ).json()
        assert len(page2["items"]) == 1
        assert page2["next_cursor"] is None

        # No overlap between pages
        ids_page1 = {i["id"] for i in page1["items"]}
        ids_page2 = {i["id"] for i in page2["items"]}
        assert ids_page1.isdisjoint(ids_page2)

    def test_total_reflects_filters(self, client, three_issues, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?status=backlog",
            headers=owner["headers"],
        )
        assert res.json()["total"] == 1


class TestIssueSearch:
    def test_search_by_title(self, client, three_issues, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?q=Alpha",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        body = res.json()
        assert body["total"] == 1
        assert body["items"][0]["title"] == "Alpha"

    def test_search_by_description(self, client, project, org_with_admin, owner):
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/",
            json={"title": "Generic Title", "description": "xyzuniquekeyword"},
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?q=xyzuniquekeyword",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        assert res.json()["total"] == 1

    def test_search_no_match(self, client, three_issues, project, org_with_admin, owner):
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?q=zzznomatch",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        assert res.json()["total"] == 0

    def test_search_combined_with_filter(self, client, three_issues, project, org_with_admin, owner):
        # Alpha is todo; search for Alpha but filter status=in_progress → 0 results
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/?q=Alpha&status=in_progress",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        assert res.json()["total"] == 0


class TestIssueDetailResponse:
    def test_get_detail_includes_comments_and_activity(
        self, client, issue, project, org_with_admin, owner
    ):
        # add a comment
        client.post(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}/comments",
            json={"content": "LGTM"},
            headers=owner["headers"],
        )
        res = client.get(
            f"/orgs/{org_with_admin['id']}/projects/{project['id']}/issues/{issue['id']}",
            headers=owner["headers"],
        )
        assert res.status_code == 200
        body = res.json()
        assert "comments" in body
        assert len(body["comments"]) == 1
        assert body["comments"][0]["content"] == "LGTM"
        assert "activity_logs" in body

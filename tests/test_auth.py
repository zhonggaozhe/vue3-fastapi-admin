import pytest


@pytest.mark.asyncio
async def test_login_success(client):
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin", "device_id": "test-device"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    data = payload["data"]
    assert data["user"]["role"] == "admin"
    assert data["user"]["permissions"] == ["*.*.*"]
    assert data["session"]["sid"].startswith("sess_")


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_user_list_endpoint(client):
    response = await client.get("/users/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    users = payload["data"]
    assert len(users) == 2
    assert next(user for user in users if user["username"] == "admin")["roles"][0]["code"] == "admin"


@pytest.mark.asyncio
async def test_menu_routes_endpoint(client):
    response = await client.get("/menus/routes", params={"username": "admin"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    routes = payload["data"]
    assert routes and routes[0]["path"] == "/dashboard"
    assert routes[0]["meta"]["title"] == "router.dashboard"


@pytest.mark.asyncio
async def test_menu_admin_list_and_crud(client):
    # list
    response = await client.get("/menus/")
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    assert payload["data"]["list"]

    create_payload = {
        "type": 0,
        "parentId": None,
        "name": "TestMenu",
        "component": "#",
        "path": "/test-menu",
        "redirect": "/test-menu",
        "status": 1,
        "meta": {
            "title": "测试菜单",
            "icon": "vi-test",
            "alwaysShow": True,
            "noCache": False,
            "breadcrumb": True,
            "affix": False,
            "noTagsView": False,
            "canTo": False,
            "hidden": False,
            "activeMenu": None
        },
        "permissionList": [
            {"label": "查看", "value": "view"}
        ]
    }

    response = await client.post("/menus/", json=create_payload)
    assert response.status_code == 200
    created = response.json()["data"]
    assert created["name"] == "TestMenu"
    menu_id = created["id"]
    action_id = created["permissionList"][0]["id"]

    update_payload = {
        **create_payload,
        "meta": {
            **create_payload["meta"],
            "title": "测试菜单-修改"
        },
        "permissionList": [
            {"id": action_id, "label": "查看", "value": "view"}
        ]
    }

    response = await client.put(f"/menus/{menu_id}", json=update_payload)
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["meta"]["title"] == "测试菜单-修改"

    response = await client.delete(f"/menus/{menu_id}")
    assert response.status_code == 200

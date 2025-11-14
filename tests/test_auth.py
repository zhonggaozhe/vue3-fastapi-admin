import pytest

from app.core.settings import get_settings


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
    assert data["routes"]


@pytest.mark.asyncio
async def test_login_invalid_password(client):
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "wrong"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 401


@pytest.mark.asyncio
async def test_account_lock_after_failed_attempts(client):
    limit = get_settings().login_failure_limit
    for attempt in range(limit):
        response = await client.post(
            "/auth/login",
            json={"username": "test", "password": "wrong"},
        )
        payload = response.json()
        assert response.status_code == 200
        if attempt < limit - 1:
            assert payload["code"] == 401
        else:
            assert payload["code"] == 423

    response = await client.post(
        "/auth/login",
        json={"username": "test", "password": "test"},
    )
    assert response.status_code == 200
    assert response.json()["code"] == 423


@pytest.mark.asyncio
async def test_user_list_endpoint(client):
    token = await _login_and_get_token(client)
    response = await client.get("/users/list", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    users = payload["data"]
    assert users  # 至少存在普通用户
    assert all(user["username"] != "admin" for user in users)


@pytest.mark.asyncio
async def test_menu_routes_endpoint(client):
    token = await _login_and_get_token(client)
    response = await client.get(
        "/menus/routes", params={"username": "admin"}, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    routes = payload["data"]
    assert routes and routes[0]["path"] == "/dashboard"
    assert routes[0]["meta"]["title"] == "router.dashboard"


@pytest.mark.asyncio
async def test_menu_admin_list_and_crud(client):
    token = await _login_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}
    # list
    response = await client.get("/menus/list", headers=headers)
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

    response = await client.post("/menus/save", json=create_payload, headers=headers)
    assert response.status_code == 200
    created = response.json()["data"]
    assert created["name"] == "TestMenu"
    menu_id = created["id"]
    action_id = created["permissionList"][0]["id"]

    update_payload = {
        **create_payload,
        "id": menu_id,
        "meta": {
            **create_payload["meta"],
            "title": "测试菜单-修改"
        },
        "permissionList": [
            {"id": action_id, "label": "查看", "value": "view"}
        ]
    }

    response = await client.post("/menus/edit", json=update_payload, headers=headers)
    assert response.status_code == 200
    updated = response.json()["data"]
    assert updated["meta"]["title"] == "测试菜单-修改"

    response = await client.post("/menus/del", json={"ids": [menu_id]}, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0


@pytest.mark.asyncio
async def test_super_admin_role_protected(client):
    token = await _login_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # 更新超级管理员角色应失败
    response = await client.post(
        "/roles/edit",
        json={
            "id": 1,
            "roleName": "Administrator",
            "role": "admin",
            "remark": "should fail",
            "status": 1,
            "menuIds": []
        },
        headers=headers,
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 400
    assert payload["message"] == "SUPER_ADMIN_IMMUTABLE"

    # 创建同名角色也应失败
    response = await client.post(
        "/roles/save",
        json={
            "roleName": "Administrator",
            "role": "admin",
            "remark": "duplicate",
            "status": 1,
            "menuIds": []
        },
        headers=headers,
    )
    data = response.json()
    assert data["code"] == 400
    assert data["message"] == "SUPER_ADMIN_RESERVED"


@pytest.mark.asyncio
async def test_user_save_edit_delete(client):
    token = await _login_and_get_token(client)
    headers = {"Authorization": f"Bearer {token}"}

    base_payload = {
        "username": "接口测试用户",
        "account": "apitestuser",
        "email": "apitest@example.com",
        "department": {"id": 101},
        "role": [2],
        "password": "apitest123"
    }

    response = await client.post("/users/save", json=base_payload, headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert payload["code"] == 0
    user_id = payload["data"]["id"]

    # use save for edit
    save_update_payload = {
        **base_payload,
        "id": user_id,
        "email": "apitest-updated@example.com"
    }
    response = await client.post("/users/save", json=save_update_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # explicit edit endpoint
    edit_payload = {
        **base_payload,
        "id": user_id,
        "account": "apitestuser",
        "email": "apitest-edit@example.com"
    }
    response = await client.post("/users/edit", json=edit_payload, headers=headers)
    assert response.status_code == 200
    assert response.json()["code"] == 0

    # delete
    response = await client.post("/users/del", json={"ids": [user_id]}, headers=headers)
    assert response.status_code == 200
    delete_payload = response.json()
    assert delete_payload["code"] == 0
    assert delete_payload["data"]["deleted"] == 1


async def _login_and_get_token(client) -> str:
    response = await client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin"},
    )
    data = response.json()["data"]
    return data["tokens"]["accessToken"]

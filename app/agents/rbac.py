from app.agents.identity import AuthenticatedUser


class RBACAgent:
    async def build_principal(self, user: AuthenticatedUser) -> dict:
        primary = user.primary_role
        principal = {
            "role": primary.code if primary else "guest",
            "roleId": str(primary.id) if primary else "",
            "permissions": user.permissions,
            "username": user.username,
        }
        if user.attributes:
            principal["attributes"] = user.attributes
        return principal

    async def is_allowed(
        self, user: AuthenticatedUser, resource: str, action: str, namespace: str | None = None
    ) -> bool:
        if user.is_superuser or "*.*.*" in user.permissions:
            return True

        target_namespace = namespace or ""
        for perm in user.permissions:
            if self._matches_permission(perm, target_namespace, resource, action):
                return True
        return False

    @staticmethod
    def _matches_permission(
        permission: str, namespace: str, resource: str, action: str
    ) -> bool:
        parts = permission.split(":")

        if len(parts) == 2:
            perm_resource, perm_action = parts
            return perm_resource in (resource, "*") and perm_action in (action, "*")

        if len(parts) == 3:
            perm_namespace, perm_resource, perm_action = parts
            return (
                perm_namespace in (namespace, "*")
                and perm_resource in (resource, "*")
                and perm_action in (action, "*")
            )

        return False

from app.agents.identity import AuthenticatedUser


class RBACAgent:
    async def build_principal(self, user: AuthenticatedUser) -> dict:
        primary = user.primary_role
        return {
            "role": primary.code if primary else "guest",
            "roleId": str(primary.id) if primary else "",
            "permissions": user.permissions,
        }

    async def is_allowed(self, user: AuthenticatedUser, resource: str, action: str) -> bool:
        if user.is_superuser or "*.*.*" in user.permissions:
            return True
        token = f"{resource}:{action}"
        return any(perm == token or perm.endswith(":*") for perm in user.permissions)

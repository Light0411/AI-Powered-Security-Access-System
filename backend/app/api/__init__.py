from fastapi import APIRouter

from .routes import admin, admin_upgrades, analytics, auth, client, face, gate_admin, gates, guests, inference, parking, pass_applications

api_router = APIRouter()
api_router.include_router(inference.router, prefix="/infer", tags=["inference"])
api_router.include_router(gates.router, prefix="/access-events", tags=["access-events"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(gate_admin.router, prefix="/admin/gates", tags=["gates"])
api_router.include_router(guests.router, prefix="/guest", tags=["guest"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(face.router, prefix="/face", tags=["face"])
api_router.include_router(client.router, prefix="/client", tags=["client"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(parking.router, prefix="/parking", tags=["parking"])
api_router.include_router(admin_upgrades.router, prefix="/admin/role-upgrades", tags=["role-upgrades"])
api_router.include_router(pass_applications.router, prefix="/admin/pass-applications", tags=["pass-applications"])

__all__ = ["api_router"]

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status

from app.core.passes import list_pass_plans
from app.schemas import (
    APIMessage,
    Pass,
    PassCreate,
    PassPlan,
    PassUpdate,
    User,
    UserCreate,
    UserUpdate,
    Vehicle,
    VehicleCreate,
    VehicleUpdate,
)
from app.services.datastore import db

router = APIRouter()


# Users -----------------------------------------------------------------
def _cors_response() -> Response:
    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        },
    )


@router.options("/users", include_in_schema=False)
def options_users() -> Response:
    return _cors_response()


@router.get("/users", response_model=list[User])
def list_users() -> list[User]:
    return db.list_users()


@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate) -> User:
    return db.create_user(payload)


@router.put("/users/{user_id}", response_model=User)
def update_user(user_id: str, payload: UserUpdate) -> User:
    try:
        return db.update_user(user_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")


@router.delete("/users/{user_id}", response_model=APIMessage)
def delete_user(user_id: str) -> APIMessage:
    try:
        db.delete_user(user_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="User not found")
    return APIMessage(message="User removed")


# Vehicles ---------------------------------------------------------------
@router.options("/vehicles", include_in_schema=False)
def options_vehicles() -> Response:
    return _cors_response()


@router.get("/vehicles", response_model=list[Vehicle])
def list_vehicles() -> list[Vehicle]:
    return db.list_vehicles()


@router.post("/vehicles", response_model=Vehicle, status_code=status.HTTP_201_CREATED)
def create_vehicle(payload: VehicleCreate) -> Vehicle:
    try:
        return db.create_vehicle(payload)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown user_id {exc.args[0]}")


@router.put("/vehicles/{vehicle_id}", response_model=Vehicle)
def update_vehicle(vehicle_id: str, payload: VehicleUpdate) -> Vehicle:
    try:
        return db.update_vehicle(vehicle_id, payload)
    except KeyError as exc:
        detail = "Vehicle not found" if exc.args[0] == vehicle_id else f"Unknown user_id {exc.args[0]}"
        raise HTTPException(status_code=404, detail=detail)


@router.delete("/vehicles/{vehicle_id}", response_model=APIMessage)
def delete_vehicle(vehicle_id: str) -> APIMessage:
    try:
        db.delete_vehicle(vehicle_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Vehicle not found")
    return APIMessage(message="Vehicle removed")


# Passes ----------------------------------------------------------------
@router.options("/passes", include_in_schema=False)
def options_passes() -> Response:
    return _cors_response()


@router.get("/passes/plans", response_model=list[PassPlan])
def list_pass_plans_endpoint() -> list[PassPlan]:
    return [
        PassPlan(
            plan_type=plan.plan_type,
            label=plan.label,
            duration_days=plan.duration_days,
            price_rm=plan.price_rm,
        )
        for plan in list_pass_plans()
    ]


@router.get("/passes", response_model=list[Pass])
def list_passes() -> list[Pass]:
    return db.list_passes()


@router.post("/passes", response_model=Pass, status_code=status.HTTP_201_CREATED)
def create_pass(payload: PassCreate) -> Pass:
    try:
        return db.create_pass(payload)
    except KeyError as exc:
        raise HTTPException(status_code=400, detail=f"Unknown user_id {exc.args[0]}")


@router.put("/passes/{pass_id}", response_model=Pass)
def update_pass(pass_id: str, payload: PassUpdate) -> Pass:
    try:
        return db.update_pass(pass_id, payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Pass not found")


@router.delete("/passes/{pass_id}", response_model=APIMessage)
def delete_pass(pass_id: str) -> APIMessage:
    try:
        db.delete_pass(pass_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Pass not found")
    return APIMessage(message="Pass removed")
@router.options("/vehicles", include_in_schema=False)
def options_vehicles() -> Response:
    return _cors_response()
@router.options("/passes", include_in_schema=False)
def options_passes() -> Response:
    return _cors_response()

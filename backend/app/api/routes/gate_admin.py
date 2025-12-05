from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import APIMessage, Gate, GateCreate, GateUpdate
from app.services.datastore import db

router = APIRouter()


@router.get("", response_model=list[Gate])
@router.get("/", response_model=list[Gate])
def list_gates() -> list[Gate]:
    return db.list_gates()


@router.post("", response_model=Gate, status_code=status.HTTP_201_CREATED)
def create_gate(payload: GateCreate) -> Gate:
    try:
        return db.create_gate(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/{gate_id}", response_model=Gate)
def update_gate(gate_id: str, payload: GateUpdate) -> Gate:
    try:
        return db.update_gate(gate_id, payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gate not found")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.delete("/{gate_id}", response_model=APIMessage)
def delete_gate(gate_id: str) -> APIMessage:
    try:
        db.delete_gate(gate_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Gate not found")
    return APIMessage(message="Gate removed")

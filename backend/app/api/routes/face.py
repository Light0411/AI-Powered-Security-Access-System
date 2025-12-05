from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import FaceEnrollRequest, FaceEnrollResponse, FaceVerifyRequest, FaceVerifyResponse, UserFace
from app.services.face_recognition import face_recognition_service

router = APIRouter()


@router.post("/enroll", response_model=FaceEnrollResponse, status_code=status.HTTP_201_CREATED)
def enroll_face(payload: FaceEnrollRequest) -> FaceEnrollResponse:
    try:
        return face_recognition_service.enroll(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post("/verify", response_model=FaceVerifyResponse)
def verify_face(payload: FaceVerifyRequest) -> FaceVerifyResponse:
    try:
        return face_recognition_service.verify(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/profiles", response_model=list[UserFace])
def list_profiles() -> list[UserFace]:
    return face_recognition_service.list_profiles()

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.schemas import (
    APIMessage,
    ParkingEventRequest,
    ParkingOverview,
    ParkingVenueCreate,
    ParkingVenueStatus,
    ParkingVenueUpdate,
)
from app.services.datastore import db

router = APIRouter()


@router.get("/overview", response_model=ParkingOverview)
def overview() -> ParkingOverview:
    return db.get_parking_overview()


@router.get("/venues", response_model=list[ParkingVenueStatus])
def list_venues() -> list[ParkingVenueStatus]:
    return db.list_parking_venues()


@router.post("/venues", response_model=ParkingVenueStatus, status_code=status.HTTP_201_CREATED)
def create_venue(payload: ParkingVenueCreate) -> ParkingVenueStatus:
    try:
        return db.create_parking_venue(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.put("/venues/{venue_id}", response_model=ParkingVenueStatus)
def update_venue(venue_id: str, payload: ParkingVenueUpdate) -> ParkingVenueStatus:
    try:
        return db.update_parking_venue(venue_id, payload)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking venue not found")


@router.delete("/venues/{venue_id}", response_model=APIMessage)
def delete_venue(venue_id: str) -> APIMessage:
    try:
        db.delete_parking_venue(venue_id)
    except KeyError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parking venue not found")
    return APIMessage(message="Venue removed")


@router.post("/event", response_model=ParkingVenueStatus)
def record_event(payload: ParkingEventRequest) -> ParkingVenueStatus:
    try:
        return db.record_parking_event(payload)
    except KeyError:
        raise HTTPException(status_code=404, detail="Parking venue not found")

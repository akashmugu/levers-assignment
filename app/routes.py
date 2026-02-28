from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session

from app.database import get_session
from app.schemas import BillCreate, BillRead
from app.services import create_bill, get_bills

router = APIRouter(prefix="/bills", tags=["bills"])


@router.post("", response_model=BillRead, status_code=201)
def create_bill_endpoint(
    bill_data: BillCreate,
    session: Session = Depends(get_session),
):
    try:
        bill = create_bill(session, bill_data)
        return bill
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="A sub_bill with this reference already exists (case-insensitive).",
        )


@router.get("", response_model=list[BillRead])
def get_bills_endpoint(
    reference: str | None = Query(
        default=None,
        description="Case-insensitive substring match on sub_bill reference",
    ),
    total_from: float | None = Query(
        default=None,
        description="Minimum total (inclusive)",
    ),
    total_to: float | None = Query(
        default=None,
        description="Maximum total (inclusive)",
    ),
    session: Session = Depends(get_session),
):
    return get_bills(
        session,
        reference=reference,
        total_from=total_from,
        total_to=total_to,
    )

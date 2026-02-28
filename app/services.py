from sqlalchemy import func
from sqlalchemy.orm import contains_eager
from sqlmodel import Session, select

from app.models import Bill, SubBill
from app.schemas import BillCreate


def create_bill(session: Session, bill_data: BillCreate) -> Bill:
    bill = Bill(total=bill_data.total)
    for sb in bill_data.sub_bills:
        sub_bill = SubBill(amount=sb.amount, reference=sb.reference)
        bill.sub_bills.append(sub_bill)
    session.add(bill)
    session.commit()
    session.refresh(bill)
    return bill


def get_bills(
    session: Session,
    *,
    reference: str | None = None,
    total_from: float | None = None,
    total_to: float | None = None,
) -> list[Bill]:
    if reference is not None:
        return _get_bills_with_reference_filter(
            session, reference, total_from, total_to
        )
    return _get_bills_without_reference_filter(session, total_from, total_to)


def _get_bills_without_reference_filter(
    session: Session,
    total_from: float | None,
    total_to: float | None,
) -> list[Bill]:
    stmt = select(Bill)
    if total_from is not None:
        stmt = stmt.where(Bill.total >= total_from)
    if total_to is not None:
        stmt = stmt.where(Bill.total <= total_to)
    stmt = stmt.order_by(Bill.id)
    return list(session.exec(stmt).all())


def _get_bills_with_reference_filter(
    session: Session,
    reference: str,
    total_from: float | None,
    total_to: float | None,
) -> list[Bill]:
    """Return bills with only the sub_bills whose reference matches.

    Uses contains_eager so SQLAlchemy populates bill.sub_bills from the
    filtered JOIN result rather than issuing a separate selectin query.
    """
    escaped = reference.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    pattern = f"%{escaped}%"

    stmt = (
        select(Bill)
        .join(Bill.sub_bills)
        .where(func.lower(SubBill.reference).like(func.lower(pattern), escape="\\"))
        .options(contains_eager(Bill.sub_bills))
        .execution_options(populate_existing=True)
    )

    if total_from is not None:
        stmt = stmt.where(Bill.total >= total_from)
    if total_to is not None:
        stmt = stmt.where(Bill.total <= total_to)

    stmt = stmt.order_by(Bill.id, SubBill.id)

    return list(session.exec(stmt).unique().all())

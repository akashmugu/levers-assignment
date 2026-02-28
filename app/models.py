from sqlalchemy import Index, text
from sqlmodel import Field, Relationship, SQLModel


class Bill(SQLModel, table=True):
    __tablename__ = "bills"

    id: int | None = Field(default=None, primary_key=True)
    total: float = Field(nullable=False)

    sub_bills: list["SubBill"] = Relationship(
        back_populates="bill",
        sa_relationship_kwargs={
            "cascade": "all, delete-orphan",
            "lazy": "selectin",
        },
    )


class SubBill(SQLModel, table=True):
    __tablename__ = "sub_bills"
    __table_args__ = (
        Index(
            "ix_sub_bills_reference_lower",
            text("lower(reference)"),
            unique=True,
            postgresql_where=text("reference IS NOT NULL"),
        ),
    )

    id: int | None = Field(default=None, primary_key=True)
    amount: float = Field(nullable=False)
    reference: str | None = Field(default=None, max_length=255)
    bill_id: int = Field(foreign_key="bills.id", nullable=False)

    bill: Bill | None = Relationship(back_populates="sub_bills")

from pydantic import BaseModel, Field, field_validator, model_validator


class SubBillCreate(BaseModel):
    amount: float
    reference: str | None = Field(default=None, max_length=255)


class SubBillRead(BaseModel):
    id: int
    amount: float
    reference: str | None = None

    model_config = {"from_attributes": True}


class BillCreate(BaseModel):
    total: float
    sub_bills: list[SubBillCreate]

    @field_validator("sub_bills")
    @classmethod
    def at_least_one_sub_bill(cls, v: list[SubBillCreate]) -> list[SubBillCreate]:
        if not v:
            raise ValueError("A bill must have at least one sub_bill")
        return v

    @model_validator(mode="after")
    def total_matches_sum(self) -> "BillCreate":
        expected = sum(sb.amount for sb in self.sub_bills)
        if abs(self.total - expected) > 1e-9:
            raise ValueError(
                f"total ({self.total}) does not match "
                f"sum of sub_bill amounts ({expected})"
            )
        return self


class BillRead(BaseModel):
    id: int
    total: float
    sub_bills: list[SubBillRead]

    model_config = {"from_attributes": True}

# Billing Service

A minimal billing microservice built with FastAPI, SQLModel, PostgreSQL, and Alembic.

## Quick Start

```bash
docker compose up --build
```

The API is available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set up PostgreSQL and configure .env
cp .env.example .env
# Edit .env with your database URL

# Run migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --reload
```

## API Endpoints

### POST /bills

Creates a bill with associated sub-bills.

**Request**

```json
{
  "total": 3,
  "sub_bills": [
    { "amount": 1, "reference": "REF-1" },
    { "amount": 2, "reference": "ref-2" }
  ]
}
```

**Response** `201 Created`

```json
{
  "id": 1,
  "total": 3,
  "sub_bills": [
    { "id": 1, "amount": 1, "reference": "REF-1" },
    { "id": 2, "amount": 2, "reference": "ref-2" }
  ]
}
```

### GET /bills

Returns bills with sub-bills. Supports optional query parameters:

| Parameter    | Description                                                                                   |
| ------------ | --------------------------------------------------------------------------------------------- |
| `reference`  | Case-insensitive substring match on sub_bill reference. Only matching sub-bills are returned. |
| `total_from` | Minimum total (inclusive)                                                                     |
| `total_to`   | Maximum total (inclusive)                                                                     |

**Example:** `GET /bills?reference=ref`

```json
[
  {
    "id": 1,
    "total": 3,
    "sub_bills": [
      { "id": 1, "amount": 1, "reference": "REF-1" },
      { "id": 2, "amount": 2, "reference": "ref-2" }
    ]
  }
]
```

## Testing

```bash
docker compose --profile test run --rm test && docker compose down
```

Integration tests against real PostgreSQL — not mocks. The service layer is thin; the interesting behavior lives in SQL: filtered JOINs, case-insensitive `LIKE` matching, unique index enforcement, and filter composition.

## Assumptions & Design Decisions

| Decision                                       | Detail                                                                                                                            |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **Total = sum of amounts**                     | Mismatch → 422. Enforced at API boundary.                                                                                         |
| **Case-insensitive unique reference**          | Partial functional index on `lower(reference) WHERE reference IS NOT NULL`. More portable than `citext`.                          |
| **Reference filter returns partial sub-bills** | Only matching sub-bills appear per bill. Bills with zero matches are excluded. Single-query via `contains_eager` + filtered JOIN. |
| **Duplicate reference → 409**                  | Case-insensitive. `"REF-1"` and `"ref-1"` conflict.                                                                               |
| **`amount` has no sign constraint**            | Negative sub-bill amounts are accepted. The spec does not prohibit them; enforcement would require a DB check constraint.         |

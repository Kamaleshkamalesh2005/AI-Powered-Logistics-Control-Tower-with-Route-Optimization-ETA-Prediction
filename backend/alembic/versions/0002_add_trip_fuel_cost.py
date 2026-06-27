"""add trip fuel cost

Revision ID: 0002_add_trip_fuel_cost
Revises: 0001_initial_logistics_schema
Create Date: 2026-06-27 00:00:00.000001

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0002_add_trip_fuel_cost"
down_revision = "0001_initial_logistics_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("trips", sa.Column("fuel_cost_inr", sa.Numeric(12, 2), nullable=True))


def downgrade() -> None:
    op.drop_column("trips", "fuel_cost_inr")
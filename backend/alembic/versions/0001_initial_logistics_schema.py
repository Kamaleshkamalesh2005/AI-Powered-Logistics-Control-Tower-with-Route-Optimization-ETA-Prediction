"""initial logistics schema

Revision ID: 0001_initial_logistics_schema
Revises:
Create Date: 2026-06-27 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_initial_logistics_schema"
down_revision = None
branch_labels = None
depends_on = None


user_role = sa.Enum("admin", "dispatcher", "viewer", name="user_role")
driver_status = sa.Enum("active", "inactive", "on_leave", name="driver_status")
vehicle_status = sa.Enum("available", "in_transit", "maintenance", "offline", name="vehicle_status")
shipment_status = sa.Enum(
    "created",
    "planned",
    "in_transit",
    "delivered",
    "exception",
    "cancelled",
    name="shipment_status",
)
trip_status = sa.Enum(
    "planned",
    "dispatched",
    "in_progress",
    "completed",
    "delayed",
    "cancelled",
    name="trip_status",
)
route_stop_status = sa.Enum("pending", "arrived", "completed", "skipped", "delayed", name="route_stop_status")
delay_severity = sa.Enum("low", "medium", "high", "critical", name="delay_severity")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("password_hash", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("email", name=op.f("uq_users_email")),
    )
    op.create_index(op.f("ix_users_created_at"), "users", ["created_at"], unique=False)
    op.create_index(op.f("ix_users_role"), "users", ["role"], unique=False)

    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("employee_code", sa.String(length=64), nullable=False),
        sa.Column("first_name", sa.String(length=80), nullable=False),
        sa.Column("last_name", sa.String(length=80), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone_number", sa.String(length=40), nullable=True),
        sa.Column("license_number", sa.String(length=64), nullable=False),
        sa.Column("license_expiry", sa.Date(), nullable=True),
        sa.Column("home_base", sa.String(length=120), nullable=True),
        sa.Column("status", driver_status, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_drivers_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_drivers")),
        sa.UniqueConstraint("employee_code", name=op.f("uq_drivers_employee_code")),
        sa.UniqueConstraint("email", name=op.f("uq_drivers_email")),
        sa.UniqueConstraint("license_number", name=op.f("uq_drivers_license_number")),
        sa.UniqueConstraint("user_id", name=op.f("uq_drivers_user_id")),
    )
    op.create_index(op.f("ix_drivers_created_at"), "drivers", ["created_at"], unique=False)
    op.create_index(op.f("ix_drivers_status"), "drivers", ["status"], unique=False)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("fleet_number", sa.String(length=64), nullable=False),
        sa.Column("license_plate", sa.String(length=32), nullable=False),
        sa.Column("vin", sa.String(length=64), nullable=True),
        sa.Column("make", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=80), nullable=True),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("capacity_kg", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", vehicle_status, nullable=False),
        sa.Column("assigned_driver_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_driver_id"], ["drivers.id"], name=op.f("fk_vehicles_assigned_driver_id_drivers"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vehicles")),
        sa.UniqueConstraint("fleet_number", name=op.f("uq_vehicles_fleet_number")),
        sa.UniqueConstraint("license_plate", name=op.f("uq_vehicles_license_plate")),
        sa.UniqueConstraint("vin", name=op.f("uq_vehicles_vin")),
        sa.UniqueConstraint("assigned_driver_id", name=op.f("uq_vehicles_assigned_driver_id")),
    )
    op.create_index(op.f("ix_vehicles_created_at"), "vehicles", ["created_at"], unique=False)
    op.create_index(op.f("ix_vehicles_status"), "vehicles", ["status"], unique=False)

    op.create_table(
        "trips",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trip_number", sa.String(length=64), nullable=False),
        sa.Column("route_name", sa.String(length=160), nullable=True),
        sa.Column("status", trip_status, nullable=False),
        sa.Column("planned_departure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_departure_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=True),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name=op.f("fk_trips_vehicle_id_vehicles"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name=op.f("fk_trips_driver_id_drivers"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_trips_created_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trips")),
        sa.UniqueConstraint("trip_number", name=op.f("uq_trips_trip_number")),
    )
    op.create_index(op.f("ix_trips_created_at"), "trips", ["created_at"], unique=False)
    op.create_index(op.f("ix_trips_status"), "trips", ["status"], unique=False)

    op.create_table(
        "shipments",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("reference", sa.String(length=64), nullable=False),
        sa.Column("origin", sa.String(length=120), nullable=False),
        sa.Column("destination", sa.String(length=120), nullable=False),
        sa.Column("customer_name", sa.String(length=160), nullable=True),
        sa.Column("status", shipment_status, nullable=False),
        sa.Column("eta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_pickup_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("planned_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_delivery_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("vehicle_id", sa.Integer(), nullable=True),
        sa.Column("driver_id", sa.Integer(), nullable=True),
        sa.Column("trip_id", sa.Integer(), nullable=True),
        sa.Column("created_by_user_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["vehicle_id"], ["vehicles.id"], name=op.f("fk_shipments_vehicle_id_vehicles"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["driver_id"], ["drivers.id"], name=op.f("fk_shipments_driver_id_drivers"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name=op.f("fk_shipments_trip_id_trips"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], name=op.f("fk_shipments_created_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_shipments")),
        sa.UniqueConstraint("reference", name=op.f("uq_shipments_reference")),
    )
    op.create_index(op.f("ix_shipments_created_at"), "shipments", ["created_at"], unique=False)
    op.create_index(op.f("ix_shipments_status"), "shipments", ["status"], unique=False)

    op.create_table(
        "route_stops",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("stop_sequence", sa.Integer(), nullable=False),
        sa.Column("location_name", sa.String(length=160), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("planned_arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_arrival_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", route_stop_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name=op.f("fk_route_stops_trip_id_trips"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_route_stops")),
        sa.UniqueConstraint("trip_id", "stop_sequence", name=op.f("uq_route_stops_trip_sequence")),
    )
    op.create_index(op.f("ix_route_stops_created_at"), "route_stops", ["created_at"], unique=False)
    op.create_index(op.f("ix_route_stops_status"), "route_stops", ["status"], unique=False)

    op.create_table(
        "delay_events",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("trip_id", sa.Integer(), nullable=False),
        sa.Column("shipment_id", sa.Integer(), nullable=True),
        sa.Column("route_stop_id", sa.Integer(), nullable=True),
        sa.Column("reported_by_user_id", sa.Integer(), nullable=True),
        sa.Column("severity", delay_severity, nullable=False),
        sa.Column("delay_minutes", sa.Integer(), nullable=False),
        sa.Column("reason_code", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["trip_id"], ["trips.id"], name=op.f("fk_delay_events_trip_id_trips"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"], name=op.f("fk_delay_events_shipment_id_shipments"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["route_stop_id"], ["route_stops.id"], name=op.f("fk_delay_events_route_stop_id_route_stops"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["reported_by_user_id"], ["users.id"], name=op.f("fk_delay_events_reported_by_user_id_users"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_delay_events")),
    )
    op.create_index(op.f("ix_delay_events_created_at"), "delay_events", ["created_at"], unique=False)
    op.create_index(op.f("ix_delay_events_severity"), "delay_events", ["severity"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_delay_events_severity"), table_name="delay_events")
    op.drop_index(op.f("ix_delay_events_created_at"), table_name="delay_events")
    op.drop_table("delay_events")

    op.drop_index(op.f("ix_route_stops_status"), table_name="route_stops")
    op.drop_index(op.f("ix_route_stops_created_at"), table_name="route_stops")
    op.drop_table("route_stops")

    op.drop_index(op.f("ix_shipments_status"), table_name="shipments")
    op.drop_index(op.f("ix_shipments_created_at"), table_name="shipments")
    op.drop_table("shipments")

    op.drop_index(op.f("ix_trips_status"), table_name="trips")
    op.drop_index(op.f("ix_trips_created_at"), table_name="trips")
    op.drop_table("trips")

    op.drop_index(op.f("ix_vehicles_status"), table_name="vehicles")
    op.drop_index(op.f("ix_vehicles_created_at"), table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index(op.f("ix_drivers_status"), table_name="drivers")
    op.drop_index(op.f("ix_drivers_created_at"), table_name="drivers")
    op.drop_table("drivers")

    op.drop_index(op.f("ix_users_role"), table_name="users")
    op.drop_index(op.f("ix_users_created_at"), table_name="users")
    op.drop_table("users")

    delay_severity.drop(op.get_bind(), checkfirst=True)
    route_stop_status.drop(op.get_bind(), checkfirst=True)
    trip_status.drop(op.get_bind(), checkfirst=True)
    shipment_status.drop(op.get_bind(), checkfirst=True)
    vehicle_status.drop(op.get_bind(), checkfirst=True)
    driver_status.drop(op.get_bind(), checkfirst=True)
    user_role.drop(op.get_bind(), checkfirst=True)
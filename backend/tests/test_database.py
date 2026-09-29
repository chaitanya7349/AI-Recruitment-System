from sqlalchemy import inspect, text

from app.database.database import engine
from app.database.models import (
    Application,
    ApplicationStatusHistory,
    CandidateProfile,
    Company,
    Job,
    NotificationItem,
    TalentPoolEntry,
    User,
)


def test_database_connection():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        value = result.scalar()

    assert value == 1


def test_required_tables_exist():
    inspector = inspect(engine)

    tables = set(inspector.get_table_names())

    required_tables = {
        "users",
        "companies",
        "candidate_profiles",
        "jobs",
        "applications",
        "application_status_history",
        "talent_pool",
        "notification_items",
    }

    missing_tables = required_tables - tables

    assert not missing_tables, (
        f"Missing database tables: {sorted(missing_tables)}"
    )


def test_models_have_expected_table_names():
    assert User.__tablename__ == "users"
    assert Company.__tablename__ == "companies"
    assert CandidateProfile.__tablename__ == "candidate_profiles"
    assert Job.__tablename__ == "jobs"
    assert Application.__tablename__ == "applications"
    assert (
        ApplicationStatusHistory.__tablename__
        == "application_status_history"
    )
    assert TalentPoolEntry.__tablename__ == "talent_pool"
    assert NotificationItem.__tablename__ == "notification_items"


def test_database_engine_is_postgresql():
    assert engine.dialect.name == "postgresql"

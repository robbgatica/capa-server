"""Database models and session management."""
import json
from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Integer, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
from app.config import settings


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class Analysis(Base):
    """Analysis result model."""
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)

    # Analysis metadata
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")  # pending, processing, completed, failed

    # ClamAV scan results
    clamav_scanned: Mapped[Optional[bool]] = mapped_column(Integer, default=False)  # SQLite uses 0/1 for bool
    clamav_status: Mapped[Optional[str]] = mapped_column(String(50))  # clean, infected, error
    clamav_signature: Mapped[Optional[str]] = mapped_column(String(255))  # Detected signature name
    clamav_scan_time: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Results
    capa_version: Mapped[Optional[str]] = mapped_column(String(50))
    rules_version: Mapped[Optional[str]] = mapped_column(String(50))
    capabilities_count: Mapped[Optional[int]] = mapped_column(Integer)
    attack_techniques: Mapped[Optional[str]] = mapped_column(Text)  # JSON array
    result_json: Mapped[Optional[str]] = mapped_column(Text)  # Full capa JSON output
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    def to_dict(self):
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "filename": self.filename,
            "file_hash": self.file_hash,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat(),
            "status": self.status,
            "clamav_scanned": bool(self.clamav_scanned),
            "clamav_status": self.clamav_status,
            "clamav_signature": self.clamav_signature,
            "clamav_scan_time": self.clamav_scan_time.isoformat() if self.clamav_scan_time else None,
            "capa_version": self.capa_version,
            "rules_version": self.rules_version,
            "capabilities_count": self.capabilities_count,
            "attack_techniques": json.loads(self.attack_techniques) if self.attack_techniques else [],
            "error_message": self.error_message,
        }

    def to_dict_with_results(self):
        """Convert to dictionary including full results."""
        data = self.to_dict()
        if self.result_json:
            data["results"] = json.loads(self.result_json)
        return data


# Database engine and session
DATABASE_URL = f"sqlite+aiosqlite:///{settings.database_path}"
engine = create_engine(f"sqlite:///{settings.database_path}", echo=settings.debug)

# Create tables
Base.metadata.create_all(engine)


def get_db():
    """Dependency for getting database sessions."""
    db = Session(engine)
    try:
        yield db
    finally:
        db.close()

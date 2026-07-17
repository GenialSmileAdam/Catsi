from sqlalchemy import String, Integer, DateTime, Text, func, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.database import Base
# from .user import User
import datetime

class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    content_type: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., 'application/pdf'
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)         # in bytes
    extracted_text: Mapped[str] = mapped_column(Text, nullable=True)        # the full parsed text
    uploaded_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    user: Mapped["User"] = relationship("User", back_populates="documents")
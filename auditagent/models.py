from sqlalchemy import Column, String, Text, DateTime
import datetime
from auditagent.db import Base

class ScanJob(Base):
    __tablename__ = "scan_jobs"

    id = Column(String, primary_key=True, index=True)
    repo_url = Column(String, index=True)
    status = Column(String, default="pending")  # pending, running, completed, failed
    webhook_url = Column(String, nullable=True)
    report_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    api_key = Column(String, index=True, nullable=True)

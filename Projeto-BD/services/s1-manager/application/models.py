from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func

Base = declarative_base()

class S1Log(Base):
    __tablename__ = "s1_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime(timezone=True), server_default=func.now())
    service = Column(String(50))        # users-service / movies-service / ratings-service
    method = Column(String(10))
    url = Column(String(255))
    request_body = Column(Text)
    response_status = Column(Integer)
    response_body = Column(Text)
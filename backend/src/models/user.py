"""
User model for authentication
Author: Héctor Alejandro Pérez (@halexespejo-cmd)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime

from src.models.database import Base


class User(Base):
    """Usuario del sistema"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Roles
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)

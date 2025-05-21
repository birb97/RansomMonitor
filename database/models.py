# database/models.py
"""
Database models for the ransomware intelligence system.

This module defines the SQLAlchemy ORM models for storing:
- Client information
- Network identifiers (watchlist)
- Ransomware claims
- Alerts generated from matches
"""

from typing import List, Dict, Any, Optional, Union, Type, TypeVar
from sqlalchemy import String, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship, sessionmaker, Session
import uuid
from datetime import datetime

Base = declarative_base()

class Client(Base):
    """
    Represents a client organization being monitored.
    
    Attributes:
        id: Primary key
        client_name: Unique name for the client
        identifiers: Collection of associated network identifiers
    """
    __tablename__ = 'clients'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    client_name: Mapped[str] = mapped_column(String, unique=True)
    
    identifiers: Mapped[List["Identifier"]] = relationship(back_populates="client")
    
    def __repr__(self) -> str:
        return f"<Client(client_name='{self.client_name}')>"

class Identifier(Base):
    """
    Represents a network identifier on the watchlist.
    
    Attributes:
        id: Primary key
        client_id: Foreign key to client
        identifier_type: Type of identifier ('name', 'ip', or 'domain')
        identifier_value: Value of the identifier
        client: Associated client
        alerts: Collection of alerts generated for this identifier
    """
    __tablename__ = 'identifiers'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey('clients.id'))
    identifier_type: Mapped[str] = mapped_column(String)  # "name", "ip", or "domain"
    identifier_value: Mapped[str] = mapped_column(String)
    
    client: Mapped["Client"] = relationship(back_populates="identifiers")
    alerts: Mapped[List["Alert"]] = relationship(back_populates="identifier")
    
    def __repr__(self) -> str:
        return f"<Identifier(type='{self.identifier_type}', value='{self.identifier_value}')>"

class Claim(Base):
    """
    Represents a ransomware claim collected from intelligence sources.
    
    Attributes:
        id: Primary key
        threat_actor: Name of the ransomware group
        source: Source of the intelligence (e.g., 'RansomLook')
        ip_network_identifier: IP address in the claim, if any
        domain_network_identifier: Domain name in the claim, if any
        name_network_identifier: Organization name in the claim
        sector: Business sector of the claimed victim
        comment: Additional information about the claim
        raw_data: Original JSON received from the source
        timestamp: When the claim was made
        claim_url: URL to the claim
        key: Unique UUID to identify the record
    """
    __tablename__ = 'claims'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    threat_actor: Mapped[str] = mapped_column(String)
    source: Mapped[str] = mapped_column(String)
    ip_network_identifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    domain_network_identifier: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    name_network_identifier: Mapped[str] = mapped_column(String)
    sector: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    comment: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    raw_data: Mapped[str] = mapped_column(String)
    timestamp: Mapped[datetime] = mapped_column()
    claim_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    key: Mapped[str] = mapped_column(String, unique=True, default=lambda: str(uuid.uuid4()))
    
    def __repr__(self) -> str:
        return f"<Claim(threat_actor='{self.threat_actor}', name='{self.name_network_identifier}')>"

class Alert(Base):
    """
    Represents an alert generated when a claim matches a watchlist identifier.
    
    Attributes:
        id: Primary key
        identifier_id: Foreign key to the matched identifier
        timestamp: When the alert was generated
        message: Alert message
        identifier: The identifier that triggered the alert
    """
    __tablename__ = 'alerts'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    identifier_id: Mapped[int] = mapped_column(ForeignKey('identifiers.id'))
    timestamp: Mapped[datetime] = mapped_column(default=datetime.now)
    message: Mapped[str] = mapped_column(String)
    
    identifier: Mapped["Identifier"] = relationship(back_populates="alerts")
    
    def __repr__(self) -> str:
        return f"<Alert(timestamp='{self.timestamp}', message='{self.message}')>"
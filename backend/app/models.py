import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String, nullable=False)
    storage_path = Column(String)
    status = Column(String, default="pending")  # pending, processing, complete, failed
    page_count = Column(Integer)
    table_count = Column(Integer, default=0)
    chart_count = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    total_latency = Column(Float, default=0.0)
    quality_score = Column(Float)
    config_bundle_version = Column(String)
    cache_hit = Column(Boolean, default=False)
    mlflow_run_id = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    stages = relationship("PipelineStage", back_populates="document", cascade="all, delete-orphan")
    result = relationship("Result", back_populates="document", uselist=False, cascade="all, delete-orphan")
    decisions = relationship("Decision", back_populates="document", cascade="all, delete-orphan")


class PipelineStage(Base):
    __tablename__ = "pipeline_stages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    stage = Column(String, nullable=False)  # classifier, text, table, chart, synthesis, quality
    status = Column(String, default="pending")  # pending, running, complete, failed, skipped
    model_used = Column(String)
    tokens_in = Column(Integer, default=0)
    tokens_out = Column(Integer, default=0)
    cost = Column(Float, default=0.0)
    latency = Column(Float, default=0.0)
    token_efficiency_ratio = Column(Float)  # tokens_out / tokens_in — prompt bloat signal
    experiment_tag = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="stages")


class Result(Base):
    __tablename__ = "results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False, unique=True)
    structured_json = Column(JSONB)
    plain_explanation = Column(Text)
    key_metrics = Column(JSONB)
    quality_detail = Column(JSONB)  # judge output: score + faithful/unfaithful claims
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="result")


class Decision(Base):
    __tablename__ = "decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id"), nullable=False)
    stage = Column(String, nullable=False)
    decision_type = Column(String, nullable=False)  # routing, model_selection, method_selection, skip
    choice_made = Column(String, nullable=False)
    alternatives_considered = Column(JSONB)
    rationale = Column(Text)
    cost_impact = Column(Float, default=0.0)  # estimated $ saved (negative) or spent vs default
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="decisions")

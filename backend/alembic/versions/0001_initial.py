"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-30

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('filename', sa.String(), nullable=False),
        sa.Column('storage_path', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('table_count', sa.Integer(), nullable=True),
        sa.Column('chart_count', sa.Integer(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('total_latency', sa.Float(), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('config_bundle_version', sa.String(), nullable=True),
        sa.Column('cache_hit', sa.Boolean(), nullable=True),
        sa.Column('mlflow_run_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'pipeline_stages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('model_used', sa.String(), nullable=True),
        sa.Column('tokens_in', sa.Integer(), nullable=True),
        sa.Column('tokens_out', sa.Integer(), nullable=True),
        sa.Column('cost', sa.Float(), nullable=True),
        sa.Column('latency', sa.Float(), nullable=True),
        sa.Column('token_efficiency_ratio', sa.Float(), nullable=True),
        sa.Column('experiment_tag', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'results',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('structured_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('plain_explanation', sa.Text(), nullable=True),
        sa.Column('key_metrics', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('quality_detail', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_id'),
    )

    op.create_table(
        'decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stage', sa.String(), nullable=False),
        sa.Column('decision_type', sa.String(), nullable=False),
        sa.Column('choice_made', sa.String(), nullable=False),
        sa.Column('alternatives_considered', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('cost_impact', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id']),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade() -> None:
    op.drop_table('decisions')
    op.drop_table('results')
    op.drop_table('pipeline_stages')
    op.drop_table('documents')

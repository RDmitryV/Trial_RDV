"""Add source verification tables

Revision ID: 001_verification
Revises:
Create Date: 2026-02-02 11:19:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_verification'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types
    op.execute("CREATE TYPE verificationstatus AS ENUM ('pending', 'verified', 'failed', 'flagged', 'outdated')")
    op.execute("CREATE TYPE reliabilityrating AS ENUM ('excellent', 'good', 'fair', 'poor', 'unreliable')")

    # Create trusted_sources table
    op.create_table(
        'trusted_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('domain', sa.String(), nullable=False, unique=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('trust_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('is_official', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('country', sa.String(), nullable=True),
        sa.Column('language', sa.String(), nullable=False, server_default='ru'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create blocked_sources table
    op.create_table(
        'blocked_sources',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('domain', sa.String(), nullable=False, unique=True),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('blocked_by', sa.String(), nullable=True),
        sa.Column('is_permanent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('unblock_date', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
    )

    # Create source_verifications table
    op.create_table(
        'source_verifications',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'verified', 'failed', 'flagged', 'outdated', name='verificationstatus'), nullable=False, server_default='pending'),
        sa.Column('reliability_rating', postgresql.ENUM('excellent', 'good', 'fair', 'poor', 'unreliable', name='reliabilityrating'), nullable=True),
        sa.Column('reliability_score', sa.Float(), nullable=True),
        sa.Column('trustworthiness_score', sa.Float(), nullable=True),
        sa.Column('content_quality_score', sa.Float(), nullable=True),
        sa.Column('last_update_check', sa.DateTime(), nullable=True),
        sa.Column('content_date', sa.DateTime(), nullable=True),
        sa.Column('is_outdated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('days_since_update', sa.Float(), nullable=True),
        sa.Column('cross_validation_count', sa.Float(), nullable=False, server_default='0'),
        sa.Column('consensus_score', sa.Float(), nullable=True),
        sa.Column('has_contradictions', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('fact_check_performed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('fact_check_passed', sa.Boolean(), nullable=True),
        sa.Column('verified_claims', sa.Float(), nullable=False, server_default='0'),
        sa.Column('total_claims', sa.Float(), nullable=False, server_default='0'),
        sa.Column('verification_notes', sa.Text(), nullable=True),
        sa.Column('issues_found', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('verification_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('verified_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_id'], ['data_sources.id'], ),
    )

    # Create data_validations table
    op.create_table(
        'data_validations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('collected_data_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_validated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('validation_status', postgresql.ENUM('pending', 'verified', 'failed', 'flagged', 'outdated', name='verificationstatus'), nullable=False, server_default='pending'),
        sa.Column('matching_sources_count', sa.Float(), nullable=False, server_default='0'),
        sa.Column('contradicting_sources_count', sa.Float(), nullable=False, server_default='0'),
        sa.Column('consensus_value', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('agreement_percentage', sa.Float(), nullable=True),
        sa.Column('validation_details', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('contradictions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('supporting_sources', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('validated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['collected_data_id'], ['collected_data.id'], ),
    )

    # Create indexes
    op.create_index('ix_source_verifications_source_id', 'source_verifications', ['source_id'])
    op.create_index('ix_source_verifications_status', 'source_verifications', ['status'])
    op.create_index('ix_data_validations_collected_data_id', 'data_validations', ['collected_data_id'])
    op.create_index('ix_data_validations_validation_status', 'data_validations', ['validation_status'])
    op.create_index('ix_trusted_sources_domain', 'trusted_sources', ['domain'])
    op.create_index('ix_blocked_sources_domain', 'blocked_sources', ['domain'])


def downgrade() -> None:
    # Drop indexes
    op.drop_index('ix_blocked_sources_domain')
    op.drop_index('ix_trusted_sources_domain')
    op.drop_index('ix_data_validations_validation_status')
    op.drop_index('ix_data_validations_collected_data_id')
    op.drop_index('ix_source_verifications_status')
    op.drop_index('ix_source_verifications_source_id')

    # Drop tables
    op.drop_table('data_validations')
    op.drop_table('source_verifications')
    op.drop_table('blocked_sources')
    op.drop_table('trusted_sources')

    # Drop enum types
    op.execute('DROP TYPE reliabilityrating')
    op.execute('DROP TYPE verificationstatus')

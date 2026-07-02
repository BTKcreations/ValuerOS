"""Initial migration

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2026-07-03

"""
from alembic import op
import sqlalchemy as sa
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False),
        sa.Column('is_active', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Create properties table
    op.create_table(
        'properties',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('parcel_number', sa.String(100), nullable=True),
        sa.Column('address_line1', sa.String(255), nullable=False),
        sa.Column('address_line2', sa.String(255), nullable=True),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(50), nullable=False),
        sa.Column('zip_code', sa.String(20), nullable=False),
        sa.Column('location', Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromText', name='geometry'), nullable=True),
        sa.Column('property_type', sa.String(50), nullable=False),
        sa.Column('sub_type', sa.String(50), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('lot_size_sqft', sa.Float(), nullable=True),
        sa.Column('gross_building_area_sqft', sa.Float(), nullable=True),
        sa.Column('bedrooms', sa.Integer(), nullable=True),
        sa.Column('bathrooms', sa.Float(), nullable=True),
        sa.Column('property_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(op.f('ix_properties_parcel_number'), 'properties', ['parcel_number'], unique=True)
    op.create_index(op.f('ix_properties_city'), 'properties', ['city'], unique=False)
    op.create_index(op.f('ix_properties_state'), 'properties', ['state'], unique=False)
    op.create_index(op.f('ix_properties_zip_code'), 'properties', ['zip_code'], unique=False)
    op.create_index(op.f('ix_properties_property_type'), 'properties', ['property_type'], unique=False)

    # Create valuations table
    op.create_table(
        'valuations',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('property_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('appraiser_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('valuation_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('effective_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('purpose', sa.String(100), nullable=True),
        sa.Column('approach', sa.String(50), nullable=True),
        sa.Column('final_value', sa.Float(), nullable=True),
        sa.Column('value_range_low', sa.Float(), nullable=True),
        sa.Column('value_range_high', sa.Float(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('methodology_notes', sa.Text(), nullable=True),
        sa.Column('adjustments', sa.JSON(), nullable=True),
        sa.Column('ml_model_version', sa.String(50), nullable=True),
        sa.Column('ml_prediction', sa.Float(), nullable=True),
        sa.Column('ml_features', sa.JSON(), nullable=True),
        sa.Column('workflow_state', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['appraiser_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
    )
    op.create_index(op.f('ix_valuations_property_id'), 'valuations', ['property_id'], unique=False)
    op.create_index(op.f('ix_valuations_appraiser_id'), 'valuations', ['appraiser_id'], unique=False)
    op.create_index(op.f('ix_valuations_status'), 'valuations', ['status'], unique=False)

    # Create comparable_sales table
    op.create_table(
        'comparable_sales',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('valuation_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('address', sa.String(255), nullable=False),
        sa.Column('city', sa.String(100), nullable=False),
        sa.Column('state', sa.String(50), nullable=False),
        sa.Column('zip_code', sa.String(20), nullable=True),
        sa.Column('location', Geometry(geometry_type='POINT', srid=4326, from_text='ST_GeomFromText', name='geometry'), nullable=True),
        sa.Column('sale_date', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sale_price', sa.Float(), nullable=True),
        sa.Column('property_type', sa.String(50), nullable=True),
        sa.Column('gross_building_area_sqft', sa.Float(), nullable=True),
        sa.Column('lot_size_sqft', sa.Float(), nullable=True),
        sa.Column('year_built', sa.Integer(), nullable=True),
        sa.Column('bedrooms', sa.Integer(), nullable=True),
        sa.Column('bathrooms', sa.Float(), nullable=True),
        sa.Column('distance_miles', sa.Float(), nullable=True),
        sa.Column('adjustment_factor', sa.Float(), nullable=True),
        sa.Column('adjusted_price', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('comp_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['valuation_id'], ['valuations.id'], ),
    )
    op.create_index(op.f('ix_comparable_sales_valuation_id'), 'comparable_sales', ['valuation_id'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('property_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('valuation_id', sa.UUID(as_uuid=False), nullable=True),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('minio_path', sa.String(500), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('doc_type', sa.String(50), nullable=True),
        sa.Column('ocr_status', sa.String(50), nullable=True),
        sa.Column('ocr_raw_text', sa.Text(), nullable=True),
        sa.Column('ocr_confidence', sa.Float(), nullable=True),
        sa.Column('extracted_data', sa.JSON(), nullable=True),
        sa.Column('embedding', Vector(1536), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], ),
        sa.ForeignKeyConstraint(['valuation_id'], ['valuations.id'], ),
    )
    op.create_index(op.f('ix_documents_property_id'), 'documents', ['property_id'], unique=False)
    op.create_index(op.f('ix_documents_valuation_id'), 'documents', ['valuation_id'], unique=False)
    op.create_index(op.f('ix_documents_ocr_status'), 'documents', ['ocr_status'], unique=False)

    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.UUID(as_uuid=False), primary_key=True),
        sa.Column('valuation_id', sa.UUID(as_uuid=False), nullable=False),
        sa.Column('status', sa.String(50), nullable=True),
        sa.Column('minio_path', sa.String(500), nullable=True),
        sa.Column('narrative', sa.Text(), nullable=True),
        sa.Column('template_version', sa.String(50), nullable=True),
        sa.Column('report_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['valuation_id'], ['valuations.id'], ),
    )
    op.create_index(op.f('ix_reports_valuation_id'), 'reports', ['valuation_id'], unique=True)


def downgrade():
    op.drop_table('reports')
    op.drop_table('documents')
    op.drop_table('comparable_sales')
    op.drop_table('valuations')
    op.drop_table('properties')
    op.drop_table('users')
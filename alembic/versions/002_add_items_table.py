"""Add items table for inventory management

Revision ID: 002
Revises: 001
Create Date: 2026-02-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create category enum type
    category_enum = sa.Enum(
        'Dairy', 'Meat', 'Seafood', 'Vegetables', 'Fruits',
        'Beverages', 'Condiments', 'Leftovers', 'Frozen', 'Other',
        name='category_enum'
    )
    category_enum.create(op.get_bind(), checkfirst=True)
    
    # Create unit enum type
    unit_enum = sa.Enum(
        'pieces', 'mL', 'L', 'g', 'kg',
        name='unit_enum'
    )
    unit_enum.create(op.get_bind(), checkfirst=True)
    
    # Create items table
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('unit', unit_enum, nullable=False, server_default='pieces'),
        sa.Column('expiry_date', sa.String(), nullable=False),
        sa.Column('category', category_enum, nullable=False),
        sa.Column('household_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['household_id'], ['households.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_items_id'), 'items', ['id'], unique=False)
    op.create_index('ix_items_category', 'items', ['category'], unique=False)
    op.create_index('ix_items_expiry_date', 'items', ['expiry_date'], unique=False)
    op.create_index('ix_items_category_expiry', 'items', ['category', 'expiry_date'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_items_category_expiry', table_name='items')
    op.drop_index('ix_items_expiry_date', table_name='items')
    op.drop_index('ix_items_category', table_name='items')
    op.drop_index(op.f('ix_items_id'), table_name='items')
    op.drop_table('items')
    
    # Drop enums
    unit_enum = sa.Enum('pieces', 'mL', 'L', 'g', 'kg', name='unit_enum')
    unit_enum.drop(op.get_bind(), checkfirst=True)
    
    category_enum = sa.Enum(
        'Dairy', 'Meat', 'Seafood', 'Vegetables', 'Fruits',
        'Beverages', 'Condiments', 'Leftovers', 'Frozen', 'Other',
        name='category_enum'
    )
    category_enum.drop(op.get_bind(), checkfirst=True)

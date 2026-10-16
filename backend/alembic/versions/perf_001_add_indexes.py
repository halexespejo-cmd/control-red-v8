"""
Performance indexes on key columns
Author: Héctor Alejandro Pérez (@halexespejo-cmd)

Revision ID: perf_001
Create Date: 2026-10-16
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = 'perf_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes"""
    
    # Devices table indexes
    op.create_index('idx_device_mac', 'devices', ['mac'], unique=True)
    op.create_index('idx_device_ip', 'devices', ['ip'])
    op.create_index('idx_device_category', 'devices', ['category'])
    op.create_index('idx_device_status', 'devices', ['is_blocked', 'is_whitelisted'])
    op.create_index('idx_device_last_seen', 'devices', ['last_seen'])
    
    # Users table indexes
    op.create_index('idx_user_username', 'users', ['username'], unique=True)
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    op.create_index('idx_user_active_admin', 'users', ['is_active', 'is_admin'])
    
    # Composite indexes for common queries
    op.create_index(
        'idx_device_category_blocked',
        'devices',
        ['category', 'is_blocked']
    )
    op.create_index(
        'idx_device_ip_last_seen',
        'devices',
        ['ip', 'last_seen']
    )


def downgrade():
    """Remove performance indexes"""
    
    # Devices indexes
    op.drop_index('idx_device_mac', 'devices')
    op.drop_index('idx_device_ip', 'devices')
    op.drop_index('idx_device_category', 'devices')
    op.drop_index('idx_device_status', 'devices')
    op.drop_index('idx_device_last_seen', 'devices')
    
    # Users indexes
    op.drop_index('idx_user_username', 'users')
    op.drop_index('idx_user_email', 'users')
    op.drop_index('idx_user_active_admin', 'users')
    
    # Composite indexes
    op.drop_index('idx_device_category_blocked', 'devices')
    op.drop_index('idx_device_ip_last_seen', 'devices')

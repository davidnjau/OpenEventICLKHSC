"""Add khsc_uid to ticket_holders for KHSC ↔ Open Event sync

Revision ID: a1b2c3d4e5f6
Revises: e7e952b58504
Create Date: 2026-04-01 00:00:00
"""

from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'e7e952b58504'


def upgrade():
    op.add_column(
        'ticket_holders',
        sa.Column('khsc_uid', sa.String(), nullable=True),
    )
    op.create_index(
        'ix_ticket_holders_khsc_uid', 'ticket_holders', ['khsc_uid'], unique=False
    )


def downgrade():
    op.drop_index('ix_ticket_holders_khsc_uid', table_name='ticket_holders')
    op.drop_column('ticket_holders', 'khsc_uid')

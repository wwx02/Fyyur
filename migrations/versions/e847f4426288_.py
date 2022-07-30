"""empty message

Revision ID: e847f4426288
Revises: 4d4c915b5b0a
Create Date: 2022-07-27 19:45:27.148911

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e847f4426288'
down_revision = '4d4c915b5b0a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Show', 'upcoming')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Show', sa.Column('upcoming', sa.BOOLEAN(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###

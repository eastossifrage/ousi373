"""initial migration

Revision ID: 14d90443ed4b
Revises: 50c433224bd7
Create Date: 2015-07-21 16:15:03.198642

"""

# revision identifiers, used by Alembic.
revision = '14d90443ed4b'
down_revision = '50c433224bd7'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('confirmed', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'confirmed')
    ### end Alembic commands ###
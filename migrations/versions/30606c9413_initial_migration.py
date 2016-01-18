"""initial migration

Revision ID: 30606c9413
Revises: 58bb1c0c03d6
Create Date: 2015-08-12 18:20:30.974412

"""

# revision identifiers, used by Alembic.
revision = '30606c9413'
down_revision = '58bb1c0c03d6'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('albums', sa.Column('picture_url', sa.String(length=128), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('albums', 'picture_url')
    ### end Alembic commands ###

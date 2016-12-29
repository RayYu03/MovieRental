"""initial migration

Revision ID: 0fa3feeb530b
Revises: fead7b9c18b4
Create Date: 2016-12-27 20:45:41.883451

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0fa3feeb530b'
down_revision = 'fead7b9c18b4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('movies', sa.Column('alt', sa.String(length=64), nullable=True))
    op.add_column('movies', sa.Column('casts', sa.String(length=64), nullable=True))
    op.add_column('movies', sa.Column('counts', sa.Integer(), nullable=True))
    op.add_column('movies', sa.Column('directors', sa.String(length=64), nullable=True))
    op.add_column('movies', sa.Column('genres', sa.String(length=64), nullable=True))
    op.add_column('movies', sa.Column('year', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('movies', 'year')
    op.drop_column('movies', 'genres')
    op.drop_column('movies', 'directors')
    op.drop_column('movies', 'counts')
    op.drop_column('movies', 'casts')
    op.drop_column('movies', 'alt')
    # ### end Alembic commands ###

"""Generating migration for a PRAW object

Revision ID: 960085fce39c
Revises: 4d46b88366fc
Create Date: 2016-06-13 17:30:49.056215

"""

# revision identifiers, used by Alembic.
revision = '960085fce39c'
down_revision = '4d46b88366fc'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_development():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('praw_keys',
    sa.Column('id', sa.String(256), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('access_token', sa.String(256), nullable=True),
    sa.Column('scope', sa.String(256), nullable=True),
    sa.Column('refresh_token', sa.String(256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade_development():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('praw_keys')
    ### end Alembic commands ###


def upgrade_test():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('praw_keys',
    sa.Column('id', sa.String(256), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('access_token', sa.String(256), nullable=True),
    sa.Column('scope', sa.String(256), nullable=True),
    sa.Column('refresh_token', sa.String(256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade_test():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('praw_keys')
    ### end Alembic commands ###


def upgrade_production():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('praw_keys',
    sa.Column('id', sa.String(256), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('access_token', sa.String(256), nullable=True),
    sa.Column('scope', sa.String(), nullable=True),
    sa.Column('refresh_token', sa.String(256), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    ### end Alembic commands ###


def downgrade_production():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('praw_keys')
    ### end Alembic commands ###


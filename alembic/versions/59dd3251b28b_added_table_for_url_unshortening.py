"""added table for url unshortening

Revision ID: 59dd3251b28b
Revises: dc2328901c69
Create Date: 2018-01-13 12:02:37.703995

"""

# revision identifiers, used by Alembic.
revision = '59dd3251b28b'
down_revision = 'dc2328901c69'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade(engine_name):
    globals()["upgrade_%s" % engine_name]()


def downgrade(engine_name):
    globals()["downgrade_%s" % engine_name]()





def upgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lumen_notice_expanded_urls',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('notice_id', sa.BigInteger(), nullable=True),
    sa.Column('original_url', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('expanded_url', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('number_of_hops', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lumen_notice_expanded_urls_notice_id'), 'lumen_notice_expanded_urls', ['notice_id'], unique=False)
    # ### end Alembic commands ###


def downgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_lumen_notice_expanded_urls_notice_id'), table_name='lumen_notice_expanded_urls')
    op.drop_table('lumen_notice_expanded_urls')
    # ### end Alembic commands ###


def upgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lumen_notice_expanded_urls',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('notice_id', sa.BigInteger(), nullable=True),
    sa.Column('original_url', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('expanded_url', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('number_of_hops', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lumen_notice_expanded_urls_notice_id'), 'lumen_notice_expanded_urls', ['notice_id'], unique=False)
    # ### end Alembic commands ###


def downgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_lumen_notice_expanded_urls_notice_id'), table_name='lumen_notice_expanded_urls')
    op.drop_table('lumen_notice_expanded_urls')
    # ### end Alembic commands ###


def upgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lumen_notice_expanded_urls',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('notice_id', sa.BigInteger(), nullable=True),
    sa.Column('original_url', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('expanded_url', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('number_of_hops', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lumen_notice_expanded_urls_notice_id'), 'lumen_notice_expanded_urls', ['notice_id'], unique=False)
    op.create_index('ix_comments_subreddit_id_created_at', 'comments', ['subreddit_id', 'created_at'], unique=False)
    # ### end Alembic commands ###


def downgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_comments_subreddit_id_created_at', table_name='comments')
    op.drop_index(op.f('ix_lumen_notice_expanded_urls_notice_id'), table_name='lumen_notice_expanded_urls')
    op.drop_table('lumen_notice_expanded_urls')
    # ### end Alembic commands ###

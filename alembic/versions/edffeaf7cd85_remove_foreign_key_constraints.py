"""remove foreign key constraints

Revision ID: edffeaf7cd85
Revises: 9dce37322c71
Create Date: 2016-06-21 16:52:25.598280

"""

# revision identifiers, used by Alembic.
revision = 'edffeaf7cd85'
down_revision = '9dce37322c71'
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
    op.drop_constraint('posts_ibfk_1', 'posts', type_='foreignkey')
    ### end Alembic commands ###


def downgrade_development():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('posts_ibfk_1', 'posts', 'subreddits', ['subreddit_id'], ['id'])
    ### end Alembic commands ###


def upgrade_test():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('posts_ibfk_1', 'posts', type_='foreignkey')
    ### end Alembic commands ###

def downgrade_test():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('posts_ibfk_1', 'posts', 'subreddits', ['subreddit_id'], ['id'])
    ### end Alembic commands ###


def upgrade_production():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('posts_ibfk_1', 'posts', type_='foreignkey')
    ### end Alembic commands ###


def downgrade_production():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_foreign_key('posts_ibfk_1', 'posts', 'subreddits', ['subreddit_id'], ['id'])
    ### end Alembic commands ###



"""create lumen twitter tables

Revision ID: 04b7c595daf2
Revises: 16dbded8a5cf
Create Date: 2017-04-27 18:55:11.873606

"""

# revision identifiers, used by Alembic.
revision = '04b7c595daf2'
down_revision = '16dbded8a5cf'
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
    op.create_table('lumen_notice_to_twitter_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notice_id', sa.BigInteger(), nullable=True),
    sa.Column('twitter_username', sa.String(length=256), nullable=True),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=True),
    sa.Column('CS_account_queried', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_notice_id'), 'lumen_notice_to_twitter_user', ['notice_id'], unique=False)
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_twitter_user_id'), 'lumen_notice_to_twitter_user', ['twitter_user_id'], unique=False)
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_twitter_username'), 'lumen_notice_to_twitter_user', ['twitter_username'], unique=False)
    op.create_table('lumen_notices',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('date_received', sa.DateTime(), nullable=True),
    sa.Column('sender', sa.String(length=256), nullable=True),
    sa.Column('principal', sa.String(length=256), nullable=True),
    sa.Column('recipient', sa.String(length=256), nullable=True),
    sa.Column('notice_data', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('CS_parsed_usernames', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('twitter_statuses',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('status_data', mysql.MEDIUMTEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_statuses_user_id'), 'twitter_statuses', ['user_id'], unique=False)
    op.create_table('twitter_user_snapshots',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('user_state', sa.Integer(), nullable=True),
    sa.Column('user_json', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('statuses_count', sa.Integer(), nullable=True),
    sa.Column('followers_count', sa.Integer(), nullable=True),
    sa.Column('friends_count', sa.Integer(), nullable=True),
    sa.Column('verified', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_user_snapshots_twitter_user_id'), 'twitter_user_snapshots', ['twitter_user_id'], unique=False)
    op.create_table('twitter_users',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('screen_name', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('lang', sa.String(length=32), nullable=True),
    sa.Column('user_state', sa.Integer(), nullable=True),
    sa.Column('CS_most_tweets_queried', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_users_screen_name'), 'twitter_users', ['screen_name'], unique=False)
    # ### end Alembic commands ###


def downgrade_development():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_twitter_users_screen_name'), table_name='twitter_users')
    op.drop_table('twitter_users')
    op.drop_index(op.f('ix_twitter_user_snapshots_twitter_user_id'), table_name='twitter_user_snapshots')
    op.drop_table('twitter_user_snapshots')
    op.drop_index(op.f('ix_twitter_statuses_user_id'), table_name='twitter_statuses')
    op.drop_table('twitter_statuses')
    op.drop_table('lumen_notices')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_twitter_username'), table_name='lumen_notice_to_twitter_user')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_twitter_user_id'), table_name='lumen_notice_to_twitter_user')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_notice_id'), table_name='lumen_notice_to_twitter_user')
    op.drop_table('lumen_notice_to_twitter_user')
    # ### end Alembic commands ###


def upgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lumen_notice_to_twitter_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notice_id', sa.BigInteger(), nullable=True),
    sa.Column('twitter_username', sa.String(length=256), nullable=True),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=True),
    sa.Column('CS_account_queried', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_notice_id'), 'lumen_notice_to_twitter_user', ['notice_id'], unique=False)
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_twitter_user_id'), 'lumen_notice_to_twitter_user', ['twitter_user_id'], unique=False)
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_twitter_username'), 'lumen_notice_to_twitter_user', ['twitter_username'], unique=False)
    op.create_table('lumen_notices',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('date_received', sa.DateTime(), nullable=True),
    sa.Column('sender', sa.String(length=256), nullable=True),
    sa.Column('principal', sa.String(length=256), nullable=True),
    sa.Column('recipient', sa.String(length=256), nullable=True),
    sa.Column('notice_data', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('CS_parsed_usernames', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('twitter_statuses',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('status_data', mysql.MEDIUMTEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_statuses_user_id'), 'twitter_statuses', ['user_id'], unique=False)
    op.create_table('twitter_users',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('screen_name', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('lang', sa.String(length=32), nullable=True),
    sa.Column('user_state', sa.Integer(), nullable=True),
    sa.Column('CS_most_tweets_queried', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_users_screen_name'), 'twitter_users', ['screen_name'], unique=False)
    # ### end Alembic commands ###


def downgrade_test():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_twitter_users_screen_name'), table_name='twitter_users')
    op.drop_table('twitter_users')
    op.drop_index(op.f('ix_twitter_statuses_user_id'), table_name='twitter_statuses')
    op.drop_table('twitter_statuses')
    op.drop_table('lumen_notices')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_twitter_username'), table_name='lumen_notice_to_twitter_user')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_twitter_user_id'), table_name='lumen_notice_to_twitter_user')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_notice_id'), table_name='lumen_notice_to_twitter_user')
    op.drop_table('lumen_notice_to_twitter_user')
    # ### end Alembic commands ###


def upgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('lumen_notice_to_twitter_user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notice_id', sa.BigInteger(), nullable=True),
    sa.Column('twitter_username', sa.String(length=256), nullable=True),
    sa.Column('twitter_user_id', sa.String(length=64), nullable=True),
    sa.Column('CS_account_queried', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_notice_id'), 'lumen_notice_to_twitter_user', ['notice_id'], unique=False)
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_twitter_user_id'), 'lumen_notice_to_twitter_user', ['twitter_user_id'], unique=False)
    op.create_index(op.f('ix_lumen_notice_to_twitter_user_twitter_username'), 'lumen_notice_to_twitter_user', ['twitter_username'], unique=False)
    op.create_table('lumen_notices',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('date_received', sa.DateTime(), nullable=True),
    sa.Column('sender', sa.String(length=256), nullable=True),
    sa.Column('principal', sa.String(length=256), nullable=True),
    sa.Column('recipient', sa.String(length=256), nullable=True),
    sa.Column('notice_data', mysql.MEDIUMTEXT(), nullable=True),
    sa.Column('CS_parsed_usernames', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('twitter_statuses',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.String(length=64), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('status_data', mysql.MEDIUMTEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_statuses_user_id'), 'twitter_statuses', ['user_id'], unique=False)
    op.create_table('twitter_users',
    sa.Column('id', sa.String(length=64), nullable=False),
    sa.Column('screen_name', sa.String(length=256), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('lang', sa.String(length=32), nullable=True),
    sa.Column('user_state', sa.Integer(), nullable=True),
    sa.Column('CS_most_tweets_queried', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_twitter_users_screen_name'), 'twitter_users', ['screen_name'], unique=False)
    # ### end Alembic commands ###


def downgrade_production():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_twitter_users_screen_name'), table_name='twitter_users')
    op.drop_table('twitter_users')
    op.drop_index(op.f('ix_twitter_statuses_user_id'), table_name='twitter_statuses')
    op.drop_table('twitter_statuses')
    op.drop_table('lumen_notices')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_twitter_username'), table_name='lumen_notice_to_twitter_user')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_twitter_user_id'), table_name='lumen_notice_to_twitter_user')
    op.drop_index(op.f('ix_lumen_notice_to_twitter_user_notice_id'), table_name='lumen_notice_to_twitter_user')
    op.drop_table('lumen_notice_to_twitter_user')
    # ### end Alembic commands ###


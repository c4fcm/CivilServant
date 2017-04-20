# example taken from http://pythoncentral.io/introductory-tutorial-python-sqlalchemy/
import os
import sys
import simplejson as json
from utils.common import *
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, BigInteger
from sqlalchemy.dialects.mysql import MEDIUMTEXT, LONGTEXT
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import sqlalchemy
import datetime
import socket

Base = declarative_base()

class FrontPage(Base):
    __tablename__ = 'front_pages'
    id                  = Column(Integer, primary_key = True)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    page_type           = Column(Integer) # see utils/common.py
    page_data           = Column(MEDIUMTEXT)
    is_utc              = Column(Boolean, default=False)

class Subreddit(Base):
    __tablename__ = 'subreddits'
    id                  = Column(String(32), primary_key = True, unique=True, autoincrement=False) # subreddit id
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    name                = Column(String(32)) # display_name

class SubredditPage(Base):
    __tablename__ = 'subreddit_pages'
    id                  = Column(Integer, primary_key = True)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    subreddit_id        = Column(String(32))
    page_type           = Column(Integer) # see utils/common.py
    page_data           = Column(MEDIUMTEXT)
    is_utc              = Column(Boolean, default=False)

# TODO: just noticed there are 2 created_at columns????
class Post(Base):
    __tablename__ = 'posts'
    id                  = Column(String(32), primary_key = True, unique=True, autoincrement=False)	# post id
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    subreddit_id        = Column(String(32))	# "subreddit_id"
    created             = Column(DateTime) # "created"
    #when this record was created:
    created_at          = Column(DateTime, default=datetime.datetime.utcnow) 
    post_data           = Column(MEDIUMTEXT)	# "json_dict"
    comment_data        = Column(LONGTEXT)
    comments_queried_at = Column(DateTime, default=None)  

class ModAction(Base):
    __tablename__ = "mod_actions"
    id                  = Column(String(256), primary_key = True, unique=True, autoincrement=False)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)  
    created_utc         = Column(DateTime)
    subreddit_id        = Column(String(32), index=True)
    mod                 = Column(String(64))
    target_author       = Column(String(64), index=True)
    action              = Column(String(256))
    target_fullname     = Column(String(256))
    action_data         = Column(MEDIUMTEXT) # json_dict

class Comment(Base):
    __tablename__ = "comments"
    id                  = Column(String(256), primary_key = True, unique=True, autoincrement=False)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)  
    created_utc         = Column(DateTime)
    subreddit_id        = Column(String(32), index=True)
    post_id             = Column(String(32), index=True)
    user_id             = Column(String(64), index=True)
    comment_data        = Column(MEDIUMTEXT)

    @classmethod
    def get_comment_tree(self, db_session, sqlalchemyfilter = None):
        all_comments = {}
        all_toplevel = {}
        for comment in db_session.query(Comment).filter(sqlalchemyfilter).all():
            comment_data = json.loads(comment.comment_data)
            toplevel = comment_data['link_id'] == comment_data['parent_id']
            comment_node = CommentNode(
                id   = comment.id,
                data = comment_data,
                link_id = comment_data['link_id'],
                toplevel = toplevel)
            all_comments[comment.id] = comment_node 
            if(toplevel):
                all_toplevel[comment.id] = comment_node

        for comment in all_comments.values():
            if comment.toplevel:
                continue
            # we only care about comments in this subset
            # so drop anything not here
            try:
                parent = all_comments[comment.data['parent_id'].replace("t1_","")]
                comment.set_parent(parent)
                parent.add_child(comment)
            except:
                continue
        return {"all_comments": all_comments, "all_toplevel":all_toplevel}    

class User(Base):
    __tablename__ = 'users'
    name                = Column(String(32), primary_key = True, unique=True, autoincrement=False)   # redditor's name
    id                  = Column(String(32)) # "redditor's id"
    created             = Column(DateTime) # "created"
    first_seen          = Column(DateTime)
    last_seen           = Column(DateTime)
    user_data           = Column(MEDIUMTEXT)

class PrawKey(Base):
    __tablename__ = 'praw_keys'
    # IDs will be a string based on the assumption
    # that each device will only have one process
    # at a time handling a particular controller
    # in the format:  
    #   HOST:ENV:CONTROLLER
    # For example:
    #   hannahmore:development:FrontPageController
    id                  = Column(String(256), primary_key = True)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    access_token        = Column(String(256))
    scope               = Column(String(256)) #json
    refresh_token       = Column(String(256))
    authorized_username = Column(String(256), index=True)
    authorized_user_id  = Column(String(256), index=True)

    @classmethod
    def get_praw_id(cls, env, controller):
        host = socket.gethostname()
        return "{0}:{1}:{2}".format(host,env,controller)

class Experiment(Base):
    __tablename__ = 'experiments'
    id                  = Column(Integer, primary_key = True)
    created_at          = Column(DateTime, default=datetime.datetime.utcnow)
    name                = Column(String(256), nullable=False, index=True)
    controller          = Column(String(256), nullable=False)
    start_time          = Column(DateTime)
    end_time            = Column(DateTime)
    settings_json       = Column(MEDIUMTEXT)

class ExperimentThing(Base):
    __tablename__ = 'experiment_things'
    id                  = Column(String(256), primary_key = True)
    created_at          = Column(DateTime, default = datetime.datetime.utcnow)
    object_type         = Column(Integer)
    experiment_id       = Column(Integer, index = True)
    object_created      = Column(DateTime)
    metadata_json       = Column(MEDIUMTEXT)

class ExperimentThingSnapshot(Base):
    __tablename__ = 'experiment_thing_snapshots'
    id                  = Column(Integer, primary_key = True)
    experiment_thing_id = Column(String(256), index = True)
    created_at          = Column(DateTime, default = datetime.datetime.utcnow)
    object_type         = Column(Integer)
    experiment_id       = Column(Integer, index = True)
    metadata_json       = Column(MEDIUMTEXT)

class ExperimentAction(Base):
    __tablename__ = 'experiment_actions'
    id                  = Column(Integer, primary_key = True)
    created_at          = Column(DateTime, default = datetime.datetime.utcnow)
    experiment_id       = Column(Integer, index = True)
    praw_key_id         = Column(String(256), index = True)
    action              = Column(String(64), index = True)
    action_subject_type = Column(String(64))
    action_subject_id   = Column(String(256), index=True)
    action_object_type  = Column(String(64))
    action_object_id    = Column(String(256), index=True)
    metadata_json       = Column(MEDIUMTEXT)


# TODO: index cols!
class LumenNotice(Base):
    __tablename__ = 'lumen_notices'
    id                  = Column(BigInteger, primary_key = True)
    date_received       = Column(DateTime, default=datetime.datetime.utcnow)
    sender              = Column(String(256))
    principal           = Column(String(256))
    recipient           = Column(String(256))
    #num_infringing_urls = Column(Integer)
    notice_data         = Column(MEDIUMTEXT)
    CS_parsed_usernames    = Column(Boolean, default=False)

# TODO: don't do foreign keys??
class LumenNoticeToTwitterUser(Base):
    __tablename__ = 'lumen_notice_to_twitter_user'
    id                  = Column(Integer, primary_key = True)    
    notice_id           = Column(Integer)
    twitter_username    = Column(String(256), index = True)
    twitter_user_id     = Column(String(256), index = True) # how long? 
    CS_account_queried    = Column(Boolean, default=False)

class TwitterUser(Base):
    __tablename__ = 'twitter_users'
    id = Column(BigInteger, primary_key = True) # TODO: make this a string
    screen_name = Column(String(256), index = True)
    created_at = Column(DateTime)
    lang = Column(String(64))

class TwitterUserSnapshot(Base):
    __tablename__ = 'twitter_user_snapshots'
    id = Column(BigInteger, primary_key = True) # TODO: make this a string
    created_at = #
    verified = Column(Boolean)
    user_state = Column(Integer) # utils/common.py
    user_json = Column(MEDIUMTEXT)

    statuses_count = Column(Integer)
    followers_count = Column(Integer)
    friends_count = Column(Integer)

# TODO: foreign keys????
class TwitterStatus(Base):
    __tablename__ = 'twitter_statuses'    
    id = Column(BigInteger, primary_key = True)
    user_id = Column(BigInteger, index = True) # string!
    #in_reply_to_user_id = Column(BigInteger) #string!
    is_reply = Column(Boolean) #
    created_at = Column(DateTime)
    status_data = Column(MEDIUMTEXT)

#TODO: multiple keys???
#TODO: learn of lumen's API
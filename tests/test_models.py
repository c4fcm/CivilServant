import pytest
import os
from sqlalchemy import and_, or_


## SET UP THE DATABASE ENGINE
## TODO: IN FUTURE, SET UP A TEST-WIDE DB SESSION
TEST_DIR = os.path.dirname(os.path.realpath(__file__))
ENV = os.environ['CS_ENV'] ="test"

from mock import Mock, patch
import simplejson as json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import glob, datetime
from utils.common import PageType, DbEngine
import socket

### LOAD THE CLASSES TO TEST
from app.models import *

db_session = DbEngine(os.path.join(TEST_DIR, "../", "config") + "/{env}.json".format(env=ENV)).new_session()

def clear_front_pages():
    db_session.query(Comment).delete()
    db_session.query(FrontPage).delete()
    db_session.commit()

def setup_function(function):
    clear_front_pages()

def teardown_function(function):
    clear_front_pages()

@pytest.fixture
def populate_front_pages():
    fixture_dir = os.path.join(TEST_DIR, "fixture_data")
    counter = 0
    for fn in glob.glob(fixture_dir + "/front_page_*.json"):
        with open(fn) as front_page_file:
          front_page_data = json.loads(front_page_file.read())['data']['children']
          first_item_timestamp = datetime.datetime.fromtimestamp(front_page_data[0]['data']['created'])
          print(type(FrontPage.page_type))
          front_page = FrontPage(created_at = first_item_timestamp,
                                 page_type = PageType.TOP.value,
                                 page_data = json.dumps(front_page_data),
                                 is_utc = True)
          db_session.add(front_page)
        counter += 1
    db_session.commit()
    return counter


### TEST THE MOCK SETUP AND MAKE SURE IT WORKS
def test_front_page(populate_front_pages):
    all_pages = db_session.query(FrontPage).all()
    assert len(all_pages) == 3
    assert len(json.loads(all_pages[0].page_data)) == 100

def test_16dbde_utc_migration(populate_front_pages):
    all_pages = db_session.query(FrontPage).all()
    for page in all_pages:
        assert page.is_utc == True
    
def test_get_praw_id():
    hostname = socket.gethostname()
    assert PrawKey.get_praw_id(ENV, "DummyController") == "{0}:test:DummyController".format(hostname)    

## test Comment.get_comment_tree(filter)
def test_comment_get_comment_tree():
    fixture_dir = os.path.join(TEST_DIR, "fixture_data")
    with open(os.path.join(fixture_dir, "comment_tree_0.json"),"r") as f:
        comment_json = json.loads(f.read())
    
    for comment in comment_json:
        dbcomment = Comment(
            id = comment['id'],
            created_at = datetime.datetime.utcfromtimestamp(comment['created_utc']),
            subreddit_id = comment['subreddit_id'],
            post_id = comment['link_id'],
            user_id = comment['author'],
            comment_data = json.dumps(comment)
        )
        db_session.add(dbcomment)
    db_session.commit()

    ## TEST BASE PROCESSING OF FIXTURES
    comment_tree = Comment.get_comment_tree(db_session, sqlalchemyfilter = and_(Comment.subreddit_id == comment['subreddit_id']))
    assert len(comment_tree['all_toplevel']) == 11
    assert len(comment_tree['all_comments']) == len(comment_json)
    assert len(comment_tree['all_toplevel']['d5q4kcz'].get_all_children()) == 7
    assert len(comment_tree['all_toplevel']['d5qgz1r'].get_all_children()) == 3
    assert len(comment_tree['all_toplevel']['d5o11tf'].get_all_children()) == 0

    ### TEST FILTERING
    db_session.add(
        Comment(
            id="123456789",
            subreddit_id = "987654321",
            comment_data = json.dumps({"parent_id":"abcde", "link_id":"abcde"})
        )
    )
    db_session.commit()
    ## TEST THAT THE RESULTS ARE NO DIFFERENT WHEN THERE'S A DIFFERENT SUBREDDIT ID
    comment_tree = Comment.get_comment_tree(db_session, sqlalchemyfilter = and_(Comment.subreddit_id == comment['subreddit_id']))
    assert len(comment_tree['all_toplevel']) == 11
    assert len(comment_tree['all_comments']) == len(comment_json)
    assert len(comment_tree['all_toplevel']['d5q4kcz'].get_all_children()) == 7
    assert len(comment_tree['all_toplevel']['d5qgz1r'].get_all_children()) == 3
    assert len(comment_tree['all_toplevel']['d5o11tf'].get_all_children()) == 0




    

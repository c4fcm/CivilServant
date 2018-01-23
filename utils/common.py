from enum import Enum
from functools import wraps
import cProfile, pstats
import datetime
import pathlib
import simplejson as json
from collections import namedtuple

BASE_DIR = str(pathlib.Path(__file__).parents[1])
LOGS_DIR = str(pathlib.Path(BASE_DIR, "logs"))
PROFILES_DIR = str(pathlib.Path(LOGS_DIR, "profiles"))
pathlib.Path(PROFILES_DIR).mkdir(parents=True, exist_ok=True)

DATETIME_FORMAT = "%Y%m%d%H%M%S%f"
PROFILE_FILENAME = "%s_%s_%s.%s"

class PageType(Enum):
    TOP = 1
    CONTR = 2 # controversial
    NEW = 3
    HOT = 4

class ThingType(Enum):
	SUBMISSION = 1
	COMMENT = 2
	SUBREDDIT = 3
	USER = 4
	STYLESHEET = 5

class EventWhen(Enum):
    BEFORE = 1
    AFTER = 2

class DbEngine:
	def __init__(self, config_path):
		self.config_path = config_path

	def new_session(self):
		with open(self.config_path, "r") as config:
		    DBCONFIG = json.loads(config.read())

		from sqlalchemy import create_engine
		from sqlalchemy.orm import sessionmaker
		from app.models import Base
		db_engine = create_engine("mysql://{user}:{password}@{host}/{database}".format(
		    host = DBCONFIG['host'],
		    user = DBCONFIG['user'],
		    password = DBCONFIG['password'],
		    database = DBCONFIG['database']), pool_recycle=3600)

		Base.metadata.bind = db_engine
		DBSession = sessionmaker(bind=db_engine)
		db_session = DBSession()
		return db_session

def _json_object_hook(dobj):
	dobj['json_dict'] = dobj.copy()
	X =  namedtuple('X', dobj.keys(), rename=True)
	X.remove = lambda x: None
	return(X(*dobj.values()))

def json2obj(data):
	return json.loads(data, object_hook=_json_object_hook)


class CommentNode:
	def __init__(self, id, data, link_id = None, toplevel = False, parent=None):
		self.id = id
		self.children = list()
		self.parent = parent
		self.link_id = link_id
		self.toplevel = toplevel
		self.data = data

	def add_child(self, child):
		self.children.append(child)

	def set_parent(self,parent):
		self.parent = parent

	def get_all_children(self):
		all_children = self.children
		for child in self.children:
			all_children = all_children + child.get_all_children()
		if(len(all_children)>0):
			return all_children
		else:
			return []

	def __str__(self):
		return str(self.id)

def profilable(fn):
    @wraps(fn)
    def _run_profiler(*args, **kwargs):
        if not kwargs.pop("_profile"):
            return fn(*args, **kwargs)
        
        profile = cProfile.Profile()
        start_dt = datetime.datetime.now().strftime(DATETIME_FORMAT)
        try:
            profile.enable()
            result = fn(*args, **kwargs)
        finally:
            profile.disable()
        end_dt = datetime.datetime.now().strftime(DATETIME_FORMAT)
        
        profile_filename = PROFILE_FILENAME % (start_dt, end_dt, fn.__name__, 'profile')
        stats_filename = PROFILE_FILENAME % (start_dt, end_dt, fn.__name__, 'txt')
       
        with open(pathlib.Path(PROFILES_DIR, stats_filename), "w") as f:
            stats = pstats.Stats(profile, stream=f)
            stats.print_stats()
            stats.dump_stats(pathlib.Path(PROFILES_DIR, profile_filename))
        
        return result

    return _run_profiler


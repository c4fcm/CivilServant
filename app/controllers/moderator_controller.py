import praw
import inspect, os, sys # set the BASE_DIR
import simplejson as json
import datetime
import reddit.connection
import reddit.praw_utils as praw_utils
import reddit.queries
import sqlalchemy
from utils.common import PageType
from app.models import Base, SubredditPage, Subreddit, Post, ModAction
from sqlalchemy import and_
import app.event_handler

class ModeratorController:
    def __init__(self, subreddit_name, db_session, r, log):
        self.subreddit_name = subreddit_name
        self.db_session = db_session
        self.log = log
        self.r = r 


        subreddit_record = db_session.query(Subreddit).filter(Subreddit.name == self.subreddit_name).first()
        if subreddit_record:
            self.subreddit_id = subreddit_record.id
        else:
            sub = self.r.get_subreddit(self.subreddit_name)
            new_sub = Subreddit(id = sub.id, 
                                name = sub.display_name)
            self.db_session.add(new_sub)
            self.db_session.commit()
            self.subreddit_id = sub.id
                        
        # for event_handler, a list of mod action objects, set in archive_mod_action_page
        self.mod_actions = []

        # for event_handler, need a dictionary of {experiment id: experiment controller instance}.
        # if you forget this line, it's okay because when we run event_handler, it will look for this attr
        self.experiment_to_controller = app.event_handler.initialize_callee_controllers(self)

    # the reasons to call this method instead of archive_mod_action history are:
    # look only for mod_actions since the last action we've stored
    # run event hooks, e.g. update_experiment, on the mod_actions found
    #
    # this is meant to be run as a job
    def archive_new_mod_actions(self):
        last_action = self.db_session.query(ModAction).filter(
            ModAction.subreddit_id == self.subreddit_id).order_by(
            ModAction.created_at.desc()).first() # latest action
        last_action_id = last_action.id if last_action else None
        self.log.info("in archive_new_mod_actions for subreddit {0}, last_action_id={1}".format(self.subreddit_name, last_action_id))
        self.archive_mod_action_history_with_event_hooks(last_action_id)

    # uses self.mod_actions
    @app.event_handler.event_handler
    def archive_mod_action_history_with_event_hooks(self, after_id=None):
        self.archive_mod_action_history(after_id=after_id)

    # without event hooks
    # populates self.mod_actions. 
    def archive_mod_action_history(self, after_id=None):
        self.mod_actions = [] # empty this data structure that is used by event hooks

        total_actions = self.db_session.query(ModAction).filter(ModAction.subreddit_id == self.subreddit_id).count()
        first_action_count = total_actions
        pre_action_count = total_actions

        self.log.info("Fetching Moderation Action History for {subreddit}. {n} actions are currently in the archive.".format(
            subreddit = self.subreddit_name,
            n = pre_action_count))

        num_actions_stored = None
        while num_actions_stored is None or num_actions_stored > 0 :
            after_id = self.archive_mod_action_page(after_id)
            self.db_session.commit()
            total_actions = self.db_session.query(ModAction).filter(ModAction.subreddit_id == self.subreddit_id).count()
            num_actions_stored = total_actions - pre_action_count
            pre_action_count = total_actions
       
        self.log.info("Finished Fetching Moderation Action History for {subreddit}. {stored} actions were stored, with a total of {total}.".format(
            subreddit = self.subreddit_name,
            stored = total_actions - first_action_count,
            total = total_actions))

    # returns the last action id, for paging purposes
    def archive_mod_action_page(self, after_id=None):
        if(after_id):
            self.log.info("Querying moderation log for {subreddit}, after_id = {after_id}".format(
                subreddit=self.subreddit_name, after_id = after_id))
        else:
            self.log.info("Querying moderation log for {subreddit}".format(subreddit=self.subreddit_name)) 

        actions = self.r.get_mod_log(self.subreddit_name, limit = 500, params={"after": after_id})
        action_count = 0
        last_action = None
        for action in actions:
            #### TO HANDLE TEST FIXTURES
            if("json_dict" in dir(action)):
                action_dict = action.json_dict
            #### CREATE NEW OBJECT
            modaction = ModAction(
                id = action_dict['id'],
                created_utc = datetime.datetime.fromtimestamp(action_dict['created_utc']),
                subreddit_id = action_dict['sr_id36'],
                mod = action_dict['mod'],
                target_author = action_dict['target_author'],
                action = action_dict['action'],
                target_fullname = action_dict['target_fullname'],
                action_data = json.dumps(action_dict)   
            )
            # db commit
            try:
                self.db_session.add(modaction)
                self.db_session.commit()
            except (sqlalchemy.orm.exc.FlushError, sqlalchemy.exc.IntegrityError) as err:
                self.db_session.rollback()
                if("conflicts with" in err.__str__() or "Duplicate" in err.__str__()):
                    self.log.info("Some Moderator actions were already in the database. Not saving. Error: {}".format(err.__str__()))
                    print("Some Moderator actions were already in the database. Not saving.")
                else:
                    self.log.error(err.__str__())
            # pass to self.mod_actions for event hooks
            else:
                # if try does not raise an exception, then we successfully stored this in db
                # pass along to event hook by adding to class attribute
                self.mod_actions.append(action) # praw.objects.ModAction object

            last_action = action_dict
            action_count += 1

        self.log.info("Completed archive of {n} returned moderation actions for {subreddit}".format(
            n=action_count,
            subreddit = self.subreddit_name))

        if last_action:
            return last_action['id']
        else:
            return last_action

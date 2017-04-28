import simplejson as json
import datetime
from app.models import Base, LumenNotice, LumenNoticeToTwitterUser, TwitterUser
from app.controllers.twitter_controller import TwitterController
import utils.common
import requests
import app.controllers.twitter_controller
import sqlalchemy

class LumenController():
    def __init__(self, db_session, l, log):
        self.db_session = db_session
        self.l = l
        self.log = log    

    # archives lumen notices since date til now(+1day)
    def archive_lumen_notices(self, topics, date):
        nowish = datetime.datetime.utcnow() + datetime.timedelta(days=1)

        recent_notices = self.db_session.query(LumenNotice).filter(LumenNotice.date_received >= date).all()
        recent_notices_ids = set([notice.id for notice in recent_notices])

        for topic in topics:
            next_page = 1
            while next_page is not None:
                data = self.l.get_notices_to_twitter([topic], 50, next_page, date, nowish)
                
                #with open("tests/fixture_data/lumen_notices_0.json") as f:
                #    data = json.loads(f.read())
                notices_json = data["notices"]
                next_page = data["meta"]["next_page"]

                added_notices = []
                for notice in notices_json:
                    if notice["id"] not in recent_notices_ids:
                        try:
                            date_received = datetime.datetime.strptime(notice["date_received"], '%Y-%m-%dT%H:%M:%S.000Z') # expect string like "2017-04-15T22:28:26.000Z"
                            sender = (notice["sender_name"].encode("utf-8", "replace") if notice["sender_name"] else "")
                            principal = (notice["principal_name"].encode("utf-8", "replace") if notice["principal_name"] else "")
                            recipient = (notice["recipient_name"].encode("utf-8", "replace") if notice["recipient_name"] else "")
                            notice_record = LumenNotice(
                                id = notice["id"],
                                date_received = date_received,
                                sender = sender,
                                principal = principal,
                                recipient = recipient,
                                notice_data = json.dumps(notice).encode("utf-8", "replace"),
                                CS_parsed_usernames = False)
                            self.db_session.add(notice_record)
                            added_notices.append(notice)
                        except:
                            self.log.error("Error while creating LumenNotice object for notice {0}".format(notice["id"]))
                try:
                    self.db_session.commit()
                    self.log.info("Saved {0} lumen notices.".format(len(added_notices)))
                except:         
                    self.log.error("Error while saving {0} lumen notices in DB Session".format(len(added_notices)))


    """
    For all LumenNotices with CS_parsed_usernames=False, parse for twitter accounts
    """
    def query_and_parse_notices_archive_users(self):
        unparsed_notices = self.db_session.query(LumenNotice).filter(LumenNotice.CS_parsed_usernames == False).all()
        parse_notices_archive_users(unparsed_notices)

        for notice in unparsed_notices:
            notice.CS_parsed_usernames = True   # update LumenNotice
        try:
            self.db_session.commit()
            self.log.info("Updated {0} LumenNotice CS_parsed_usernames fields.".format(len(unparsed_notices)))
        except:
            self.log.error("Error while saving DB Session for updating {0} LumenNotice CS_parsed_usernames fields.".format(len(unparsed_notices)))


    """
    unparsed_notices = listo of LumenNotice
    """
    def parse_notices_archive_users(self, unparsed_notices):
        for notice in unparsed_notices:
            notice_json = json.loads(notice.notice_data) if type(notice) is LumenNotice else notice # to accomodate test fixture data
            notice_users = set([])
            suspended_user_count = 0
            for work in notice_json["works"]:
                # infringing_urls is known to contain urls
                for url_obj in work["infringing_urls"]:
                    url = url_obj["url"]
                    try:
                        username = helper_parse_url_for_username(url)    
                        if username:
                            notice_users.add(username)
                    except utils.common.ParseUsernameSuspendedUserFound:
                        suspended_user_count += 1
                if len(work["copyrighted_urls"]) > 0:  # I've only seen this empty
                    self.log.error("method helper_parse_notices_archive_users: maybe missed something in notice_json['works']['copyrighted_urls']; notice id = {0}".format(notice_json["id"]))                
                if work["description"]:  # I've only seen this null
                    self.log.error("method helper_parse_notices_archive_users: maybe missed something in notice_json['works']['description']; notice id = {0}".format(notice_json["id"]))                
            if notice_json["body"]:  # I've only seen this null
                self.log.error("method helper_parse_notices_archive_users: maybe missed something in notice_json['body']; notice id = {0}".format(notice_json["id"]))                


            existing_users = []
            if len(notice_users) > 0:
                existing_users = self.db_session.query(TwitterUser).filter(TwitterUser.screen_name.in_(list(notice_users))).all()

            # for every notice, commit LumenNoticeToTwitterUser records 
            for username in notice_users:
                notice_user_record = LumenNoticeToTwitterUser(
                        notice_id = notice_json["id"],
                        twitter_username = username.lower(),
                        twitter_user_id = None,
                        CS_account_queried = username in existing_users)
                self.db_session.add(notice_user_record)
            for i in range(suspended_user_count):
                notice_user_record = LumenNoticeToTwitterUser(
                        notice_id = notice_json["id"],
                        twitter_username = utils.common.SUSPENDED_TWITTER_USER_STR,
                        twitter_user_id = utils.common.SUSPENDED_TWITTER_USER_STR,
                        CS_account_queried = False)
                self.db_session.add(notice_user_record)                

            try:
                self.db_session.commit()
                self.log.info("Saved {0} twitter users from {1} infringing_urls in notice {2}.".format(
                    len(notice_users),
                    sum(len(work["infringing_urls"]) for work in notice_json["works"]),
                    notice_json["id"]))
            except:
                # TODO: make error messages more specific, aka Error while saving n LumenNoticeToTwitterUsers....
                self.log.error("Error while saving {0} twitter users from {1} infringing_urls in notice {2} DB Session".format(
                    len(notice_users),
                    sum(len(work["infringing_urls"]) for work in notice_json["works"]),
                    notice_json["id"]))


# assume url is of the form 'https://twitter.com/sooos243/status/852942353321140224' 
# OR check if a t.co url extends to a twitter.com url 
# interesting later study: see how many t.co links resolve to twitter links?
def helper_parse_url_for_username(url):
    twitter_domain = "twitter.com"
    tco_domain = "t.co"
    username = None
    url_split = url.split("/")

    # calling requests.get is very time inefficient
    #"""
    if len(url_split) >= 3 and url_split[2] == tco_domain:
        # try to get request and unshorten the url
        try:
            # TODO: better way to unshorten t.co links?? header-only requests??
            r = requests.get(url)
            if r:
                url = r.url
                url_split = url.split("/")
            else:
                raise Exception
        except:
            raise utils.common.ParseUsernameNoUserFound

    if url == "https://twitter.com/account/suspended":
        # TODO: then we have no information. what should we do about them? should we count these? 
        # save a LumenNoticeToTwitterUser record, with username = "SUSPENDED"
        raise utils.common.ParseUsernameSuspendedUserFound

    if len(url_split) >= 3 and url_split[2] == twitter_domain:
        username = url_split[3]
    return username

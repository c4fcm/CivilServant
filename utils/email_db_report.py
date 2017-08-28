import os, sys
import datetime
import simplejson as json

ENV = sys.argv[1] # "production"
os.environ['CS_ENV'] = ENV
BASE_DIR = os.path.join(os.path.dirname(os.path.realpath(__file__)), "..")
sys.path.append(BASE_DIR)

from utils.common import PageType, ThingType, TwitterUserState

with open(os.path.join(BASE_DIR, "config") + "/{env}.json".format(env=ENV), "r") as config:
  DBCONFIG = json.loads(config.read())

with open(os.path.join(BASE_DIR, "config") + "/email_db_report.json".format(env=ENV), "r") as config:
  EMAIL_CONFIG = json.loads(config.read())

### LOAD SQLALCHEMY
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import func

db_engine = create_engine("mysql://{user}:{password}@{host}/{database}".format(
    host = DBCONFIG['host'],
    user = DBCONFIG['user'],
    password = DBCONFIG['password'],
    database = DBCONFIG['database']))
DBSession = sessionmaker(bind=db_engine)
db_session = DBSession()

### FILTER OUT DEPRECATION WARNINGS ASSOCIATED WITH DECORATORS
# https://github.com/ipython/ipython/issues/9242
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, message='.*use @default decorator instead.*')


#####################################################


TOTAL_LABEL = "total count"
DATE_FORMAT_SEC = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT_DAY = "%Y-%m-%d"

def date_to_str(date, by_day=True):
    date_format = DATE_FORMAT_DAY if by_day else DATE_FORMAT_SEC
    return date.strftime(date_format)

def str_to_date(date_str, by_day=True):
    date_format = DATE_FORMAT_DAY if by_day else DATE_FORMAT_SEC
    return datetime.datetime.strptime(date_str, date_format)

def run_query_for_days(query_str, today, days=7):
    today_str = date_to_str(today, by_day=False)
    last_week = today - datetime.timedelta(days=days)
    last_week_str = date_to_str(last_week, by_day=False)

    result = db_session.execute(query_str, {"from_date": last_week_str, "to_date": today_str}).fetchall()
    return result

# query that doesn't take in arguments
def run_simple_query(query_str):
    result = db_session.execute(query_str).fetchall()
    return result

# result should be an iterable of primitives
# column_names should be an iterable of strings
# expects arbitrary number of columns, 2 rows (one of which is the heading)
def generate_simple_html_table(result, column_names, title):
    html = "<tr><th>{0}</th>".format(title)

    for column in column_names:
        html += "<th>{0}</th>".format(column)
    html += "</tr><tr><td></td>"

    for value in result:
        html += "<td>{0}</td>".format(value)
    html += "</tr>"

    return html

# result should be [(label, count), (label, count), (label, count)...]
# expects 2 columns, arbitrary number of rows
def generate_group_by_html_table(result, title):
    html = """
        <tr>
            <th>{0}</th>
            <th>count</th>
        </tr>            
            """.format(title)

    html += "<tr>"
    for (label, count) in result:
        html += """
            <td>{0}</td>
            <td>{1}</td>            
            """.format(label, count)
    html += "</tr>"

    return html

def transform_result_to_dict(result):
    type_to_date_to_val = {}
    for row in result:
        (this_type, year, month, day, count) = row
        date = str_to_date("{0}-{1}-{2}".format(year, month, day))
        
        if this_type not in type_to_date_to_val:
            type_to_date_to_val[this_type] = {}
        type_to_date_to_val[this_type][date] = count
    return type_to_date_to_val
    
def generate_days_html_table(result, today, title):
    d = transform_result_to_dict(result)  
    return generate_simple_html_table_from_dict(d, today, title)
    
def generate_days_html_table_from_dict(type_to_date_to_val, today, title):                
    days_str = [date_to_str(today - datetime.timedelta(days=i)) for i in range(0,7)]
    days = [str_to_date(d) for d in days_str] # to make everything 00:00:00 
    past_days = days[1:]
    html = """
        <tr>
            <th>{7}</th>
            <th>{0} (Today)</th> 
            <th>Past Mean</th>
            <th>{1}</th>
            <th>{2}</th>
            <th>{3}</th>
            <th>{4}</th>
            <th>{5}</th>
            <th>{6}</th>
        </tr>""".format(*days_str, title)
    
    for type in sorted(type_to_date_to_val.keys()):
        this_data = type_to_date_to_val[type]
        past_mean = round(sum([this_data[d] if d in this_data else 0 for d in past_days ]) / len(past_days) if len(past_days) > 0 else 0, 2)

        html += """
            <tr>
                <td>{0}</td>
                <td class='highlight'>{1}</td> 
                <td class='highlight'>{2}</td>
                <td>{3}</td>
                <td>{4}</td>
                <td>{5}</td>
                <td>{6}</td>
                <td>{7}</td>
                <td>{8}</td>                
            </tr>""".format(type,
                            (this_data[days[0]] if days[0] in this_data else 0), 
                            past_mean,
                            *[this_data[d] if d in this_data else 0 for d in past_days])
                
    return html


def send_db_report(toaddrs, date, html):
    fromaddr = EMAIL_CONFIG["fromaddr"]
    subject = "CivilServant Database Report: {0}".format(date_to_str(date))
    send_email(fromaddr, toaddrs, subject, html)

def send_email(fromaddr, toaddrs, subject, html):
    import smtplib
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText

    COMMASPACE = ', '

    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = COMMASPACE.join(toaddrs)
    msg['Subject'] = subject

    body = html
    msg.attach(MIMEText(body, 'html'))

    server = smtplib.SMTP('localhost', 25)
    text = msg.as_string()
    server.sendmail(fromaddr, toaddrs, text)
    server.quit()
    print("Sent email from {0} to {1} recipients".format(fromaddr, len(toaddrs)))


######################################################################
######### REDDIT          ############################################
######################################################################

def generate_reddit_front_page(today=datetime.datetime.utcnow(), days=7):
    #query_str = "SELECT min(created_at), max(created_at) FROM front_pages"
    #result = db_session.execute(query_str).fetchall()    
    #print(result)
    
    query_str = """
        SELECT page_type, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM front_pages WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY page_type, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    result = [(PageType(a).name, b, c, d, e) for (a,b,c,d,e) in result]
    return generate_days_html_table(result, 
        str_to_date(date_to_str(today)), 
        "New FrontPage count, by pagetype")  # to make everything 00:00:00 


def generate_reddit_subreddit_page(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT subreddit_id, page_type, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM subreddit_pages WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY subreddit_id, page_type, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    result = [("({0}, {1})".format(a, PageType(b).name), c, d, e, f) for (a,b,c,d,e,f) in result]
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New SubredditPage count, by (subreddit, pagetype)")  # to make everything 00:00:00     


def generate_reddit_subreddit(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM subreddits WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY YEAR(created_at), MONTH(created_at), DAY(created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Subreddit count")  # to make everything 00:00:00     

def generate_reddit_post(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT subreddit_id, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM posts WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY subreddit_id, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Post count, by subreddit")  # to make everything 00:00:00     

def generate_reddit_comment(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT subreddit_id, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM comments WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY subreddit_id, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Comment count, by subreddit")  # to make everything 00:00:00     


def generate_reddit_user(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(first_seen), MONTH(first_seen), DAY(first_seen), count(*) 
        FROM users WHERE first_seen <= :to_date and first_seen >= :from_date 
        GROUP BY YEAR(first_seen), MONTH(first_seen), DAY(first_seen)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New User count")  # to make everything 00:00:00     

def generate_reddit_mod_action(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT subreddit_id, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM mod_actions WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY subreddit_id, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Mod actions count")  # to make everything 00:00:00     




######################################################################
######### LUMEN, TWITTER   ###########################################
######################################################################


def generate_lumen_notices(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(date_received), MONTH(date_received), DAY(date_received), count(*) 
        FROM lumen_notices WHERE date_received <= :to_date and date_received >= :from_date 
        GROUP BY YEAR(date_received), MONTH(date_received), DAY(date_received)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Lumen Notices per day count")     

def generate_lumen_notices_collected(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at), count(*) 
        FROM lumen_notices WHERE record_created_at <= :to_date and record_created_at >= :from_date 
        GROUP BY YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Lumen Notices collected per day count")     

#job state query
def generate_lumen_notices_job_state():
    query_str = """
        SELECT CS_parsed_usernames, count(*)
        FROM lumen_notices
        GROUP BY CS_parsed_usernames
        """
    result = run_simple_query(query_str)
    return generate_group_by_html_table(
        [(TwitterUserState(label).name, count) for (label, count) in result], 
        "LumenNotices.CS_parsed_usernames")



def generate_lumen_notice_to_twitter_user_collected(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at), count(*) 
        FROM lumen_notice_to_twitter_user WHERE record_created_at <= :to_date and record_created_at >= :from_date 
        GROUP BY YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Total LumenNoticeToTwitterUser collected per day count")     


def generate_lumen_notice_to_twitter_user_incomplete(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at), count(*) 
        FROM lumen_notice_to_twitter_user WHERE record_created_at <= :to_date and record_created_at >= :from_date 
        and twitter_user_id is NULL
        GROUP BY YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "Incomplete LumenNoticeToTwitterUser per day count")     



# simple count query
def generate_lumen_notice_to_twitter_user_simple_counts():
    query_str = """
        SELECT count(*), count(notice_id), count(twitter_username)
        FROM lumen_notice_to_twitter_user
        """
    result = run_simple_query(query_str)
    return generate_simple_html_table(result, "LumenNoticeToTwitterUser counts")

# simple count query
def generate_lumen_notice_to_twitter_user_incomplete_simple_counts():
    query_str = """
        SELECT count(*), count(notice_id), count(twitter_username)
        FROM lumen_notice_to_twitter_user
        WHERE twitter_user_id is NULL
        """
    result = run_simple_query(query_str)
    return generate_simple_html_table(result, "Incomplete LumenNoticeToTwitterUser counts")


#job state query
def generate_lumen_notice_to_twitter_user_job_state():
    query_str = """
        SELECT CS_account_archived, count(*) 
        FROM lumen_notice_to_twitter_user
        GROUP BY CS_account_archived
        """
    result = run_simple_query(query_str)
    return generate_group_by_html_table(
        [(TwitterUserState(label).name, count) for (label, count) in result], 
        "LumenNoticeToTwitterUser.CS_account_archived")


def generate_twitter_user_collected(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at), count(*) 
        FROM twitter_users WHERE record_created_at <= :to_date and record_created_at >= :from_date 
        GROUP BY YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result,  
                               str_to_date(date_to_str(today)), 
                               "New Total Twitter Users collected per day count")     


#job state query
def generate_twitter_users_job_state():
    query_str = """
        SELECT CS_oldest_tweets_archived, count(*)
        FROM twitter_users
        GROUP BY CS_oldest_tweets_archived
        """
    result = run_simple_query(query_str)
    return generate_group_by_html_table(
        [(TwitterUserState(label).name, count) for (label, count) in result], 
        "TwitterUsers.CS_oldest_tweets_archived")


# simple count query
def generate_twitter_users_simple_counts():
    query_str = """
        SELECT count(*), count(screen_name) 
        FROM twitter_users
        """
    result = run_simple_query(query_str)
    return generate_simple_html_table(
        result[0], 
        ["count(*)", "count(screen_name)"], 
        "TwitterUsers counts")


# simple count query
def generate_twitter_user_snapshots_simple_counts():
    query_str = """
        SELECT count(*), count(twitter_user_id)
        FROM twitter_user_snapshots
        """
    result = run_simple_query(query_str)
    return generate_simple_html_table(
        result[0], 
        ["count(*)", "count(twitter_user_id)"],
        "TwitterUserSnapshots counts")



##### TAKES (AT LEAST) 5 MIN TO RUN...
def generate_twitter_user_snapshots_collected(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at), count(*) 
        FROM twitter_user_snapshots WHERE record_created_at <= :to_date and record_created_at >= :from_date 
        GROUP BY YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Total Twitter User Snapshots collected per day count")     

# simple count query
def generate_twitter_statuses_simple_counts():
    query_str = """
        SELECT count(*), count(user_id)
        FROM twitter_statuses
        """
    result = run_simple_query(query_str)
    return generate_simple_html_table(
        result[0], 
        ["count(*)", "count(user_id)"],
        "TwitterStatuses counts")


# ##### TOO EXPENSIVE.... probably not worth doing.
# query_str = """SELECT YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at), count(*) 
# FROM twitter_statuses WHERE record_created_at <= "2017-07-19" and record_created_at >= "2017-07-05" 
# GROUP BY YEAR(record_created_at), MONTH(record_created_at), DAY(record_created_at);"""



######################################################################
######### EXPERIMENT ###########################################
######################################################################

######### EXPERIMENT #########
def generate_experiment_new(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT '{0}', YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM experiments WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY YEAR(created_at), MONTH(created_at), DAY(created_at)""".format(TOTAL_LABEL)
    result = run_query_for_days(query_str, today, days=days)
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "New Experiment count")  # to make everything 00:00:00     

def generate_experiment_active(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT id, start_time, end_time 
        FROM experiments WHERE start_time <= :to_date and end_time >= :from_date"""
    result = run_query_for_days(query_str, today, days=days)
    type_to_date_to_val = {}
    type_to_date_to_val[TOTAL_LABEL] = {}
    days_str = [date_to_str(today - datetime.timedelta(days=i)) for i in range(0,7)]
    days = [str_to_date(d) for d in days_str] # to make everything 00:00:00 
    for day in days:
        type_to_date_to_val[TOTAL_LABEL][day] = 0
        for (eid, start, end) in result:
            if start <= day and day <= end:
                type_to_date_to_val[TOTAL_LABEL][day] += 1
    return generate_days_html_table_from_dict(type_to_date_to_val, 
                               str_to_date(date_to_str(today)), 
                               "Active Experiment count")  # to make everything 00:00:00     
    
def generate_experiment_thing(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT experiment_id, object_type, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM experiment_things WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY experiment_id, object_type, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    result = [("({0}, {1})".format(a, ThingType(b).name), c, d, e, f) for (a,b,c,d,e,f) in result]
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "ExperimentThing count, by (experiment, objecttype)")  # to make everything 00:00:00 

def generate_experiment_thing_snapshot(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT experiment_id, object_type, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM experiment_thing_snapshots WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY experiment_id, object_type, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    result = [("({0}, {1})".format(a, ThingType(b).name), c, d, e, f) for (a,b,c,d,e,f) in result]
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "ExperimentThingSnapshot count, by (experiment, objecttype)")  # to make everything 00:00:00 


def generate_experiment_action(today=datetime.datetime.utcnow(), days=7):
    query_str = """
        SELECT experiment_id, action, YEAR(created_at), MONTH(created_at), DAY(created_at), count(*) 
        FROM experiment_actions WHERE created_at <= :to_date and created_at >= :from_date 
        GROUP BY experiment_id, action, YEAR(created_at), MONTH(created_at), DAY(created_at)"""
    result = run_query_for_days(query_str, today, days=days)
    result = [("({0}, {1})".format(a, b), c, d, e, f) for (a,b,c,d,e,f) in result]
    return generate_days_html_table(result, 
                               str_to_date(date_to_str(today)), 
                               "ExperimentAction count, by (experiment, action)")  # to make everything 00:00:00 





######################################################################
######### GENERATE REPORT  ###########################################
######################################################################


css = """
<style>
table {
    border-collapse: collapse;
    width: 100%;
}

th {
    background-color:#dddddd
}

th, td {
    padding: 8px;
    text-align: left;
    border-bottom: 1px solid #ddd;
}

tr:hover{
    background-color:#f5f5f5
}

td.highlight {
    background-color:#eeeeee
}



</style>
"""


def generate_report(today=datetime.datetime.utcnow(), days=7):
    html = "<html><head>" + css + "</head><body>"
    html += "<h2>Number of records stored per day</h2>"
    #html += "<h3>Reddit:</h3>"    
    html += "<table>"
    html += generate_reddit_front_page(today, days)
    html += generate_reddit_subreddit_page(today, days)
    html += generate_reddit_subreddit(today, days)
    html += generate_reddit_post(today, days)
    html += generate_reddit_comment(today, days) 
    html += generate_reddit_user(today, days)
    html += generate_reddit_mod_action(today, days)
    #html += "<h3>Experiment:</h3>"    
    html += generate_experiment_new(today, days)
    html += generate_experiment_active(today, days)    
    html += generate_experiment_thing(today, days)
    html += generate_experiment_thing_snapshot(today, days)
    html += generate_experiment_action(today, days)    
    html += "</table>"    
    html += "</body></html>"
    return html

def generate_twitter_report(today=datetime.datetime.utcnow(), days=7):
    html = "<html><head>" + css + "</head><body>"
    html += "<h2>Number of records stored per day</h2>"

    html += "<h3>LumenNotices</h3>"    
    html += "<table>"
    html += generate_lumen_notices(today, days)
    html += generate_lumen_notices_collected(today, days)    
    html += "</table>"    
    html += "<table>" 
    html += generate_lumen_notices_job_state()
    html += "</table>"    

    html += "<h3>LumenNoticeToTwitterUsers</h3>"    
    html += "<table>"
    html += generate_lumen_notice_to_twitter_user_collected(today, days)
    html += generate_lumen_notice_to_twitter_user_incomplete(today, days)    
    html += "</table>"    
    html += "<table>" 
    html += generate_lumen_notice_to_twitter_user_job_state()
    html += "</table>"    
    html += "<table>" 
    html += generate_lumen_notice_to_twitter_user_simple_counts()
    html += generate_lumen_notice_to_twitter_user_incomplete_simple_counts()    
    html += "</table>"    

    html += "<h3>TwitterUsers</h3>"    
    html += "<table>"
    html += generate_twitter_user_collected(today, days)
    html += "</table>"    
    html += "<table>" 
    html += generate_twitter_users_job_state()
    html += "</table>"    
    html += "<table>" 
    html += generate_twitter_users_simple_counts()
    html += "</table>"    

    html += "<h3>TwitterUserSnapshots</h3>"    
    html += "<table>"
    html += generate_twitter_user_snapshots_collected(today, days)
    html += "</table>"    
    html += "<table>" 
    html += generate_twitter_user_snapshots_simple_counts()
    html += "</table>"    

    html += "<h3>TwitterStatuses</h3>"    
    html += "<table>"
    html += generate_twitter_statuses_simple_counts()
    html += "</table>"    

    html += "</body></html>"
    return html


#############################################################
#############################################################


if __name__ == "__main__":
    today = datetime.datetime.utcnow() # str_to_date("2016-08-26 23:59:59", by_day=False)
    html = generate_report(today, days=7)
    toaddrs = EMAIL_CONFIG["toaddrs"]    
    send_db_report(toaddrs, today, html)

    #print(html)
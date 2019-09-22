import time
import datetime
from peewee import *
import logging
logging.basicConfig(level=logging.INFO,
                    format='(%(module)s) %(message)s',
                    handlers=[logging.FileHandler("session.log", 'w+', 'utf-8')])
logger = logging.getLogger("Log")

db = SqliteDatabase('a.db')

def xprint(msg):
    logger.info(str(msg))
    # print(str(msg))

class BaseModel(Model):
    class Meta:
        database = db


class Account(BaseModel):
    in_work = BooleanField(default=True)
    status = CharField(default="Created account")
    user_id = IntegerField()
    login = CharField()
    password = CharField(default="None")
    code = CharField(default="None")
    proxy = CharField(default="None")
    session_name = CharField(default="None")
    updated_at = DateTimeField(default=datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"))


class Settings(BaseModel):
    key = CharField()
    value = CharField()


def create_new_user(user_id: int, login: str):
    with db:
        try:
            user = Account.create(user_id=user_id, login=login)
            return user
        except Exception as ex:
            xprint(ex)
            return None


def get_new_users(max_users: int):
    with db:
        try:
            new_users_count = Account.select().where(Account.status == "Created account", Account.in_work == True).order_by(Account.id.desc()).limit(max_users).count()
            xprint(f"Find {new_users_count} new users in db")
            if new_users_count == 0:
                return None

            new_users = Account.select().where(Account.status == "Created account", Account.in_work == True).order_by(Account.id.desc()).limit(max_users)

            for new_user in new_users:
                session_name = f"{new_user.id}_{new_user.user_id}_{new_user.login}"
                xprint(
                    f"User_id {new_user.user_id} with id {new_user.id} and login {new_user.login} to Created session with session_name {session_name}")
                new_user.status = "Created session"
                new_user.session_name = session_name
                new_user.updated_at = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
                new_user.save()
            return new_users
        except Exception as ex:
            xprint(ex)
            return None

# id; login; datetime;
def get_new_session(accs_list: list):
    with db:
        try:
            for acc in accs_list:
                acc_id = acc["id"]
                acc_login = acc["login"]

                this_acc_in_db_count = Account.select().where(Account.user_id == acc_id, Account.in_work == True).count()
                if this_acc_in_db_count > 0:
                    # xprint(f"Acc with id {acc_id} and login {acc_login} in db")
                    continue

                xprint(f"Acc with id {acc_id} and login {acc_login} NOT in db")

                create_new_user(acc_id, acc_login)
            
            pass
        except Exception as ex:
            xprint(ex)
            return None

def is_end_work():
    with db:
        try:
            end_work = Settings.get(Settings.key == "work")
            if end_work.value == "1":
                return False
            else:
                return True
        except Exception as ex:
            xprint(ex)
            return True


def session_now_reset():
    with db:
        try:
            session_now = Settings.get(Settings.key == "session_now")
            session_now.value = "0"
            session_now.save()
            return 0
        except Exception as ex:
            xprint(ex)
            return None


def get_session_max():
    with db:
        try:
            session_max = Settings.get(Settings.key == "session_max")
            return int(session_max.value)
        except Exception as ex:
            xprint(ex)
            return None


def get_session_now():
    with db:
        try:
            session_now = Settings.get(Settings.key == "session_now")
            return int(session_now.value)
        except Exception as ex:
            xprint(ex)
            return None


def session_now_plus():
    with db:
        try:
            session_now = Settings.get(Settings.key == "session_now")
            session_now.value = f"{int(session_now.value)+1}"
            session_now.save()
            return int(session_now.value)
        except Exception as ex:
            xprint(ex)
            return None

def session_now_minus():
    with db:
        try:
            session_now = Settings.get(Settings.key == "session_now")
            session_now.value = f"{int(session_now.value)-1}"
            session_now.save()
            return int(session_now.value)
        except Exception as ex:
            xprint(ex)
            return None
        
def session_can_more():
    with db:
        try:
            session_now = Settings.get(Settings.key == "session_now")
            session_max = Settings.get(Settings.key == "session_max")
            # xprint(f"Session max = {session_max.value}, session now = {session_now.value}")
            diff_sessions = int(session_max.value) - int(session_now.value)
            if diff_sessions > 0:
                return diff_sessions
            else:
                return False
        except Exception as ex:
            xprint(ex)
            return False

# db.connect()
# db.create_tables([Account, Settings])
# new_acc = Account.create(user_id=0, login="sebek@gmail.com")
# new_set_work = Settings.create(key="work", value="1")
# new_set_max = Settings.create(key="session_max", value="5")
# new_set_now = Settings.create(key="session_now", value="0")
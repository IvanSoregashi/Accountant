import requests

from collections import UserDict
from utils import *
from DynamoDB import DynamoDB

log = logging.getLogger("Account")


class Account(UserDict):
    @classmethod
    def from_email(cls, data, env):
        email = ensure_email(data)
        if not email: raise ValueError(f"{data} is not email. Operation aborted.")
        log.debug(f"Searching for {email} in the DynamoDB.")
        items = DynamoDB(env).query_user_account_by_email(email)
        if len(items) > 1:
            userIds = [x['userId'] for x in items]
            log.warning(f"More than one account found for {data}, taking the first from userIds: {userIds}")
        item = items[0]
        return cls(item)

    @classmethod
    def from_userid(cls, data):
        if not is_usrId(data): raise ValueError(f"{data} id not valid dev/qa userid. Operation aborted.")
        log.debug(f"Searching for {data} in the DynamoDB.")
        env = envron(data)
        item = DynamoDB(env).get_user_account(data)
        return cls(item)

    def refresh(self):
        userId = self.data['userId']
        env = envron(userId)
        item = DynamoDB(env).get_user_account(userId)
        self.data.update(item)
        self.data["pulled"] = ts_now()
        if "mobilePushData" in item:
            self.data["LastMobile"] = parse_pd(item)

    @classmethod
    def get_local(cls, data):
        return AccountGroup().find(data)

    def save_local(self):
        AccountGroup().data.update({self.data['userId']: self})

    def __new__(cls, item):
        if not isinstance(item, dict):
            log.critical(f"Account is not initialized with proper item: {item}")
            raise TypeError(f"Account is not initialized with proper item: {item}")
        inst = super().__new__(cls)
        inst.data = item
        inst.data.setdefault("pulled", ts_now())
        if "mobilePushData" in item:
            inst.data["LastMobile"] = parse_pd(item)
        return inst

    def __repr__(self):
        return f"{self.data["userId"]} {self.data["email"]}"

    def unmigrate(self):
        log.debug("executing unmigrate action")
        env = envron(self['userId'])
        url = REQUEST[env]['unmigrate']['url'].format(self['userId'])
        headers = REQUEST[env]['unmigrate']['headers']
        payload = REQUEST[env]['unmigrate']['payload']
        return requests.request("PUT", url, headers=headers, data=payload)

    @classmethod
    def register(cls, env, email, cc, lang, type):
        url = REQUEST[env][f'create_{type}']['url']
        headers = REQUEST[env][f'create_{type}']['headers']
        payload = REQUEST[env][f'create_{type}']['payload'].format()
        return requests.request("PUT", url, headers=headers, data=payload)


class AccountGroup(UserDict):
    _master = None

    @classmethod
    def get_accounts(cls):
        try:
            with open(accounts_json_file, "r", encoding="utf-8") as file:
                items = json.load(file)
        except OSError as e:
            log.error(f"Exception when trying to load a file '{accounts_json_file}'")
            log.exception(e)
            raise OSError(f"Exception when trying to load a file '{accounts_json_file}'")
        except json.JSONDecodeError as e:
            log.error(f"Exception when trying to read json '{accounts_json_file}'")
            log.exception(e)
            raise json.JSONDecodeError(f"Exception when trying to read json '{accounts_json_file}'")
        log.debug(f"Loaded {len(items)} accounts from disk")
        return items

    @classmethod
    def save_accounts(cls):
        try:
            with open(accounts_json_file, "w", encoding="utf-8") as file:
                json.dump(cls._master.serializable_dict, file, indent=2)
                log.info(f"Saved {len(cls._master)} accounts to disk")
        except OSError as e:
            log.error(f"Exception when trying to save a file '{accounts_json_file}'")
            log.exception(e)
            raise OSError(f"Exception when trying to save a file '{accounts_json_file}'")

    def __new__(cls, *args, **kwargs):
        if not args and not kwargs and cls._master:
            log.debug("Returning the existing master group")
            return cls._master
        log.debug("Cooking up a new Account group")
        return super().__new__(cls)

    def __init__(self, dict=None, /, **kwargs):
        if dict or kwargs: super().__init__(dict or kwargs)
        elif not self.__class__._master:
            self.data = {k: Account(v) for k, v in AccountGroup.get_accounts().items()}
            self.email_data = {acc['email']: acc for acc in self.data.values()}
            self.__class__._master = self

    def __missing__(self, key):
        log.debug(f"Key {key} was not found in UserID index")
        if is_email(key):
            log.debug(f"Checking email-index for {key}")
            return self.email_data[key]
        else:
            raise KeyError("Not Found")

    def find(self, data):
        log.debug(f"Searching for {data} locally.")
        acc = None
        if is_usrId(data):
            data_type = "UserId"
            acc = self.data.get(data, None)
        elif is_email(data):
            data_type = "email"
            acc = self.email_data.get(data, None)
        else:
            data_type = "partial email"
            for item in self.email_data:
                if data in item:
                    acc = self.email_data.get(item, None)
                    break
        if not acc: log.warning(f"Nothing was found locally with {data_type} {data}.")
        return acc

    def compile_email_index(self):
        self.email_data = {acc['email']: acc for acc in self.data.values()}

    def remove_item(self, item):
        if item in self.data:
            del self.data[item]

    def add_item(self, acc):
        if not isinstance(acc, Account):
            log.debug("Argument needs conversion, attempting")
            acc = Account(acc)
        self._master.data[acc['userId']] = acc
        if self is not self._master:
            log.debug("this group is not a master group")
            self.data['userId'] = acc

    @property
    def serializable_dict(self):
        return {k: dec_to_int(v.data) for k, v in self._master.data.items()}

    def list_repr(self):
        return "\n".join(map(repr, self.data.values()))

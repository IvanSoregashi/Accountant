from collections import UserDict
from utils import *

log = logging.getLogger("Account")


class Account_Legacy(UserDict):
    __saved_accounts = dict()

    @classmethod
    def load_from_dynamo(cls, data):
        item = Account_Legacy.find_in_dynamo(data)
        return Account_Legacy(item)

    @classmethod
    def find_in_dynamo(cls, data):
        log.debug(f"Searching for {data} in the DynamoDB.")
        if is_usrId(data):
            data_type = "UserId"
            item = cls.__aws.get_user_account(data)
        elif is_email(data):
            data_type = "email"
            items = cls.__aws.query_user_account_by_email(data)
            if len(items) > 1:
                userIds = [x['userId'] for x in items]
                log.warning(
                    f"More than one account found for {data_type} {data}, taking the first from userIds: {userIds}")
            item = items[0]
        else:
            log.error(f"Cannot use {data} to query DynamoDB")
            return
        if not item:
            log.error(f"Nothing was found in AWS({cls.__aws.env}) by {data_type} {data}.")
        return item

    @classmethod
    def find_in_local(cls, data):
        log.debug(f"Searching for {data} locally.")
        acc = None
        if is_usrId(data):
            data_type = "UserId"
            acc = cls.__saved_accounts.get(data, None)
        elif is_email(data):
            data_type = "email"
            for item in cls.__saved_accounts.values():
                if data == item.get("email"):
                    acc = item
                    break
        else:
            data_type = "partial email"
            for item in cls.__saved_accounts.values():
                if data in item.get("email"):
                    acc = item
                    break
        if not acc: log.warning(f"Nothing was found locally with {data_type} {data}.")
        return acc

    @classmethod
    def find_by_email(cls, email):
        for acc in cls.__local.accounts.values():
            if email in acc.get("email"):
                return Account_Legacy(acc)

    @classmethod
    def find_by_usrid(cls, userid):
        return cls.__saved_accounts.get(userid, None)

    @classmethod
    def set_up(cls, aws, local):
        cls.__aws = aws
        cls.__local = local
        for acc, item in cls.__local.accounts.items():
            cls.__saved_accounts[acc] = Account_Legacy(item)

    @classmethod
    def list_dicts(cls, with_field=None):
        #predicate = (lambda x: with_field in x) if not with_field else None
        #return [acc.data for acc in filter(predicate, cls.__saved_accounts.values())]
        return list(cls.__local.accounts.values())

    @classmethod
    def list_strings(cls):
        return "\n".join(map(repr, cls.__saved_accounts.values()))

    @classmethod
    def create(cls):
        # TODO or should this rather be done in a separate class?
        pass

    def __new__(cls, item):
        if not isinstance(item, dict):
            log.critical(f"Account is not initialized with proper item: {item}")
            raise ValueError(f"Account is not initialized with proper item: {item}")
        if not isinstance(cls.__saved_accounts.get(item["userId"], None), cls):
            inst = super().__new__(cls)
            inst.data = dec_to_int(item)
            inst.data.setdefault("pulled", ts_now())
            if "mobilePushData" in item:
                inst.data["LastMobile"] = parse_pd(item)
            cls.__local.accounts[item["userId"]] = inst.data
            cls.__saved_accounts[item["userId"]] = inst
        return cls.__saved_accounts[item["userId"]]

    def __repr__(self):
        return f"{self.data["userId"]}_{self.data["email"]}"

    def update_from_aws(self):
        userId = self.data["userId"]
        item = self.__class__.__aws.get_user_account(userId)
        self.data.update(item)
        self.data["pulled"] = ts_now()
        assert self.__class__.__local.accounts[userId]["pulled"] == self.data[
            "pulled"], "Local dict was not updated after update"

    def unmigrate(self):
        # TODO
        pass


class Account(UserDict):
    def __new__(cls, item):
        if not isinstance(item, dict):
            log.critical(f"Account is not initialized with proper item: {item}")
            raise ValueError(f"Account is not initialized with proper item: {item}")
        if not isinstance(..., cls):
            inst = super().__new__(cls)
            inst.data = item
            inst.data.setdefault("pulled", ts_now())
            if "mobilePushData" in item:
                inst.data["LastMobile"] = parse_pd(item)
        return inst

    def __repr__(self):
        return f"{self.data["userId"]}_{self.data["email"]}"


class AccountGroup(UserDict):
    master = None

    @classmethod
    def get_accounts(cls):
        try:
            with open(accounts_json_file, "r", encoding="utf-8") as file:
                return json.load(file)
        except OSError as e:
            log.error(f"Exception when trying to load a file '{accounts_json_file}'")
            log.exception(e)
            raise OSError(f"Exception when trying to load a file '{accounts_json_file}'")
        except json.JSONDecodeError as e:
            log.error(f"Exception when trying to read json '{accounts_json_file}'")
            log.exception(e)
            raise json.JSONDecodeError(f"Exception when trying to read json '{accounts_json_file}'")

    @classmethod
    def save_accounts(cls):
        try:
            with open(accounts_json_file, "w", encoding="utf-8") as file:
                json.dump(cls.master.serializable_dict, file, indent=2)
                log.info(f"Saved {len(cls.master)} accounts to disk")
        except OSError as e:
            log.error(f"Exception when trying to save a file '{accounts_json_file}'")
            log.exception(e)
            raise OSError(f"Exception when trying to save a file '{accounts_json_file}'")

    def __new__(cls, filter=None):
        if not cls.master:
            accounts = AccountGroup.get_accounts()
            inst = super().__new__(cls)
            inst.data = {k: Account(v) for k, v in accounts.items()}
            cls.master = inst
        if not filter:
            return cls.master
        else:
            return NotImplemented

    def __missing__(self, key):
        if is_email(key):
            userid = self.userid_from_email(key)
            return self.data[userid]
        else:
            raise KeyError("Not Found")

    def userid_from_email(self, email):
        for acc in self.data:
            if acc['email'] == email:
                return acc['userId']

    @property
    def serializable_dict(cls):
        return {k: dec_to_int(v.data) for k, v in cls.master.data.items()}

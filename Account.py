from collections import UserDict
from utils import *
from DynamoDB import DynamoDB

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
        inst = super().__new__(cls)
        inst.data = dec_to_int(item)
        inst.data.setdefault("pulled", ts_now())
        if "mobilePushData" in item:
            inst.data["LastMobile"] = parse_pd(item)
        return inst

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
    @classmethod
    def from_email(cls, data, env=None):
        log.debug(f"Searching for {data} in the DynamoDB.")
        if not is_email(data):
            log.debug(f"{data} does not look like email to me, WTF? Let's see what I can do")
            data = ensure_email(data)
            if not data:
                log.error("There was nothing I could do. Operation aborted.")
                return
        if not env: env = confirm_env()
        items = DynamoDB(env).query_user_account_by_email(data)
        if len(items) > 1:
            userIds = [x['userId'] for x in items]
            log.warning(f"More than one account found for {data}, taking the first from userIds: {userIds}")
        item = items[0]
        # TODO should all of the above evaluations really be in this class???
        return item

    @classmethod
    def from_userid(cls, data):
        log.debug(f"Searching for {data} in the DynamoDB.")
        if not is_usrId(data):
            log.error(f"{data} id not valid dev/qa userid. Operation aborted.")
            return
        env = envron(data)
        item = DynamoDB(env).get_user_account(data)
        return item

    @classmethod
    def get_local(cls, data):
        AccountGroup().find(data)

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


class AccountGroup(UserDict):
    master = None

    @classmethod
    def get_accounts(cls):
        try:
            with open(accounts_json_file, "r", encoding="utf-8") as file:
                log.debug("Collecting data from disk")
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
        log.debug("Cooking a new Account Group")
        if not cls.master:
            log.debug("No master group found, creating new master group")
            accounts = AccountGroup.get_accounts()
            inst = super().__new__(cls)
            inst.data = {k: Account(v) for k, v in accounts.items()}
            inst.email_data = {acc['email']: acc for acc in inst.data.values()}
            cls.master = inst
        if not filter:
            log.debug("Returning the Master Group")
            return cls.master
        else:
            log.debug("Filters were not yet implemented")
            return NotImplemented

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
        self.master.data[acc['userId']] = acc
        if self is not self.master:
            log.debug("this group is not a master group")
            self.data['userId'] = acc

    @property
    def serializable_dict(cls):
        return {k: dec_to_int(v.data) for k, v in cls.master.data.items()}

    @staticmethod
    def query_with_email(data):
        pass

    @staticmethod
    def query_with_usrid(data):
        pass

    def list(self):
        return "\n".join(map(repr, self.data.values()))

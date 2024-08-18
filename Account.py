import logging
from collections import UserDict

from utils import dec_to_int, is_email, parse_pd, ts_now

log = logging.getLogger("Account")


class Account(UserDict):
    __saved_accounts = dict()

    @classmethod
    def from_email(cls, email):
        items = cls.__aws.query_user_account_by_email(email)
        if not items:
            log.error(f"Nothing was found in AWS({cls.__aws.env}) by email {email}")
            return
        if len(items) > 1:
            userIds = [x['userId'] for x in items]
            log.warning(f"More than one account found for {email}, taking the first from userIds: {userIds}")
        item = items[0]
        return Account(item)

    @classmethod
    def find_by_email(cls, email):
        for acc in cls.__local.accounts.values():
            if email in acc.get("email"):
                return acc
    # TODO request info from database

    @classmethod
    def set_up(cls, aws, local):
        cls.__aws = aws
        try:
            aws.env
        except Exception as e:
            log.critical(f"AWS Class passed without initialization")
            log.exception(e)
            raise ValueError("AWS Class passed without initialization")
        cls.__local = local
        try:
            local.accounts
        except Exception as e:
            log.critical(f"Local Class passed without initialization")
            log.exception(e)
            raise ValueError("Local Class passed without initialization")
        for acc, item in cls.__local.accounts.items():
            cls.__saved_accounts[acc] = Account(item)
        # TODO I probably do not need that many checks now, or maybe, this method altogether

    @classmethod
    def is_saved(cls, string):
        if is_email(string):
            return string in [i['email'] for i in cls.__local.accounts.values()]
        else:
            return string in cls.__local.accounts

    @classmethod
    def list_dicts(cls, with_field=None):
        #predicate = (lambda x: with_field in x) if not with_field else None
        #return [acc.data for acc in filter(predicate, cls.__saved_accounts.values())]
        return list(cls.__local.accounts.values())

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

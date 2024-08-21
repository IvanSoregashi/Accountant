import logging
from collections import UserDict

from utils import dec_to_int, is_email, parse_pd, ts_now, is_usrId

log = logging.getLogger("Account")


class Account(UserDict):
    __saved_accounts = dict()

    @classmethod
    def load_from_dynamo(cls, data):
        item = Account.find_in_dynamo(data)
        return Account(item)

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
                log.warning(f"More than one account found for {data_type} {data}, taking the first from userIds: {userIds}")
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
                return Account(acc)

    @classmethod
    def find_by_usrid(cls, userid):
        return cls.__saved_accounts.get(userid, None)

    @classmethod
    def set_up(cls, aws, local):
        cls.__aws = aws
        cls.__local = local
        for acc, item in cls.__local.accounts.items():
            cls.__saved_accounts[acc] = Account(item)

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


class AccountGroup(UserDict):
    pass

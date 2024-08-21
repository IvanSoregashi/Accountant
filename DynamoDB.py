import logging
import boto3
import os

from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key
from utils import dec_to_int, expand
from obscura import *

log = logging.getLogger("DynamoDB")


class DynamoDB:
    QUERIES = 0
    INSTANCE = {}

    def __new__(cls, env):
        if not isinstance(cls.INSTANCE.get(env), cls):
            inst = super().__new__(cls)

            inst.env = env
            log.info(f"Instantiating the AWS({env}) object")
            load_dotenv(f"config/.env.{env}", override=True)

            inst.__dynamo_db_resource = boto3.resource(
                service_name='dynamodb',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('REGION_NAME')
            )

            inst.Device = inst.__dynamo_db_resource.Table("Device")
            inst.UserAccount = inst.__dynamo_db_resource.Table("UserAccount")
            inst.UserDevices = inst.__dynamo_db_resource.Table("UserDevices")

            cls.INSTANCE[env] = inst
        return cls.INSTANCE[env]

    def get_item(self, table_name, **kwargs):
        log.debug(f"AWS({self.env}).get_item called on table {table_name} with kwargs {kwargs}")
        self.__class__.QUERIES += 1
        table = self.__dynamo_db_resource.Table(table_name)
        item = table.get_item(Key=kwargs)
        item = item.get("Item", {})
        return item

    def query(self, table_name, key, value):
        log.debug(f"AWS({self.env}).query called on table {table_name} with {key}={value}")
        self.__class__.QUERIES += 1
        table = self.__dynamo_db_resource.Table(table_name)
        items = table.query(KeyConditionExpression=Key(key).eq(value))
        items = items.get("Items", [])
        return items

    def query_devices(self, parentid):
        self.__class__.QUERIES += 1
        items = self.Device.query(KeyConditionExpression=Key(parent_field).eq(parentid))
        items = items.get("Items", [])
        return items

    def query_user_devices(self, userid):
        self.__class__.QUERIES += 1
        items = self.UserDevices.query(KeyConditionExpression=Key("userId").eq(userid))
        items = items.get("Items", [])
        return items

    def get_device(self, parentid, deviceid=None):
        self.__class__.QUERIES += 1
        key = {parent_field: parentid, device_field: deviceid if deviceid else parentid}
        item = self.Device.get_item(Key=key)
        item = item.get("Item", {})
        return item

    def get_user_device(self, userid, deviceid):
        self.__class__.QUERIES += 1
        key = {"userId": userid, "deviceid": deviceid}
        item = self.UserDevices.get_item(Key=key)
        item = item.get("Item", {})
        return item

    def get_user_account(self, userid):
        self.__class__.QUERIES += 1
        key = {"userId": userid}
        item = self.UserAccount.get_item(Key=key)
        item = item.get("Item", {})
        if not item:
            log.error(f"Account with userId: {userid} was not found in AWS({self.env})")
        return dec_to_int(item)

    def query_user_account_by_email(self, email):
        self.__class__.QUERIES += 1
        items = self.UserAccount.query(IndexName="email-index", KeyConditionExpression=Key("email").eq(email))
        items = items.get("Items", {})
        if not items:
            log.error(f"Account with email: {email} was not found in AWS({self.env})")
            return
        #item = items[0]
        return dec_to_int(items)

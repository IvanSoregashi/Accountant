import logging
import boto3
import os

from dotenv import load_dotenv
from boto3.dynamodb.conditions import Key
from obscura import *

log = logging.getLogger("DynamoDB")


class DynamoDB:
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

            cls.INSTANCE[env] = inst
        return cls.INSTANCE[env]

    def get_item(self, table_name, **kwargs):
        log.debug(f"AWS({self.env}).get_item called on table {table_name} with kwargs {kwargs}")
        table = self.__dynamo_db_resource.Table(table_name)
        item = table.get_item(Key=kwargs)
        item = item.get("Item", {})
        if not item:
            log.error(f"Nothing was found in AWS({self.env}) table {table_name} with query {kwargs}")
        return item

    def query(self, table_name, key, value):
        log.debug(f"AWS({self.env}).query called on table {table_name} with {key}={value}")
        table = self.__dynamo_db_resource.Table(table_name)
        items = table.query(KeyConditionExpression=Key(key).eq(value))
        items = items.get("Items", [])
        if not items:
            log.error(f"Nothing was found in AWS({self.env}) table {table_name} with pair {key}:{value}")
        return items

    def put(self, table_name, item):
        log.debug(f"AWS({self.env}).put called on table {table_name} with {item}")
        table = self.__dynamo_db_resource.Table(table_name)
        table.put_item(Item=item)

    def query_devices(self, parentid):
        return self.query(DV, parent_field, parentid)

    def query_user_devices(self, userid):
        return self.query(UD, "userId", userid)

    def get_device(self, parentid, deviceid=None):
        deviceid = deviceid if deviceid else parentid
        return self.get_item(DV, parent_field=parentid, device_field=deviceid)

    def get_user_device(self, userid, deviceid):
        return self.get_item(UD, userId=userid, deviceid=deviceid)

    def get_user_account(self, userid):
        return self.get_item(UA, userId=userid)

    def query_user_account_by_email(self, email):
        t = self.__dynamo_db_resource.Table(UA)
        items = t.query(IndexName="email-index", KeyConditionExpression=Key("email").eq(email))
        items = items.get("Items", {})
        if not items:
            log.error(f"Account with email: {email} was not found in AWS({self.env})")
            return
        return items

    def get_device_eligibility(self, deviceid):
        return self.get_item(DE, **{device_field: deviceid})

    def put_device_eligibility(self, item):
        return self.put(DE, item)

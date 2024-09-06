import boto3
from boto3.dynamodb.conditions import Key
from utils import *

log = logging.getLogger("DynamoDB")


class DynamoDB:
    INSTANCE = {}

    def __getattribute__(self, item):
        if ENV.IS_NOT_SET():
            raise EnvironmentError("Environment is not set")
        if ENV.IS_PROD():
            raise EnvironmentError("Cannot operate with production database")
        return super().__getattribute__(item)

    def __new__(cls):
        if ENV.IS_NOT_SET():
            raise EnvironmentError("Environment is not set")
        if ENV.IS_PROD():
            raise EnvironmentError("Cannot operate with production database")

        env = ENV.GET

        if not isinstance(cls.INSTANCE.get(env), cls):
            inst = super().__new__(cls)

            log.info(f"Instantiating the AWS({env}) object")
            inst.__dynamo_db_resource = boto3.resource(
                service_name='dynamodb',
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                region_name=os.getenv('REGION_NAME')
            )

            cls.INSTANCE[env] = inst
        return cls.INSTANCE[env]

    @classmethod
    def get_item(cls, table_name, **kwargs):
        log.debug(f"AWS({ENV.GET}).get_item called on table {table_name} with kwargs {kwargs}")
        table = cls().__dynamo_db_resource.Table(table_name)
        item = table.get_item(Key=kwargs)
        item = item.get("Item", {})
        if not item:
            log.error(f"Nothing  -{item}-  was found in AWS({ENV.GET}) table {table_name} with query {kwargs}")
        return item

    @classmethod
    def query(cls, table_name, key, value):
        log.debug(f"AWS({ENV.GET}).query called on table {table_name} with {key}={value}")
        table = cls().__dynamo_db_resource.Table(table_name)
        items = table.query(KeyConditionExpression=Key(key).eq(value))
        items = items.get("Items", [])
        if not items:
            log.error(f"Nothing -{items}- was found in AWS({ENV.GET}) table {table_name} with pair {key}:{value}")
        return items

    @classmethod
    def put(cls, table_name, item):
        log.debug(f"AWS({ENV.GET}).put called on table {table_name} with {item}")
        table = cls().__dynamo_db_resource.Table(table_name)
        table.put_item(Item=item)

    @classmethod
    def query_user_account_by_email(cls, email):
        log.debug(f"AWS({ENV.GET}).query called on table {UA} with email={email}")
        table = cls().__dynamo_db_resource.Table(UA)
        items = table.query(IndexName="email-index", KeyConditionExpression=Key("email").eq(email))
        items = items.get("Items", {})
        if not items:
            log.error(f"Account with email: {email} was not found in AWS({ENV.GET})")
            return
        return items

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

    def get_device_eligibility(self, deviceid):
        return self.get_item(DE, **{device_field: deviceid})

    def put_device_eligibility(self, item):
        return self.put(DE, item)

    def query_engagements(self, userId):
        return self.query(UE, "userId", userId)

    def get_engagement(self, userId, fn):
        return self.get_item(UE, **{"userId": userId, "featureName": fn})

    def put_engagement(self, item):
        return self.put(UE, item)

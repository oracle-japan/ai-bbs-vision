import io
import json
import logging
import base64
import random
import string
import os
import oracledb
from zipfile import ZipFile
from fdk import response, context
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner, get_resource_principals_signer
from oci.ai_vision import AIServiceVisionClient
from oci.ai_vision.models import AnalyzeImageDetails, ImageClassificationFeature, InlineImageDetails
from oci.database import DatabaseClient
from oci.database.models import GenerateAutonomousDatabaseWalletDetails

# from Configs
compartment_id = os.getenv('COMPARTMENT_ID')
model_id = os.getenv('MODEL_ID')
atp_id = os.getenv('ATP_ID')
username = os.getenv('USERNAME')
dsn = os.getenv('DSN')
password = os.getenv('PASSWORD')
wallet_password = ''.join(random.choices(string.ascii_uppercase + string.digits, k=15)) # random string

wallet_zip_location = "/tmp/dbwallet.zip"
wallet_dir = "/tmp/Wallet"

is_local = os.getenv('IS_LOCAL')
is_save = os.getenv('IS_SAVE')
if "true".__eq__(is_local):
    signer = InstancePrincipalsSecurityTokenSigner()
else:
    signer = get_resource_principals_signer()

# executed once when the function container is initialized
def get_wallet():
    logging.getLogger().info("Inside get_wallet")
    atp_client = DatabaseClient(config={}, signer=signer)
    atp_wallet_details = GenerateAutonomousDatabaseWalletDetails(password=wallet_password)
    obj = atp_client.generate_autonomous_database_wallet(atp_id, atp_wallet_details)
    with open(wallet_zip_location, 'w+b') as f:
        for chunk in obj.data.raw.stream(1024 * 1024, decode_content=False):
            f.write(chunk)
    with ZipFile(wallet_zip_location, 'r') as zipObj:
        zipObj.extractall(wallet_dir)

get_wallet()

conn = oracledb.connect(
    user=username,
    password=password,
    dsn=dsn,
    wallet_location=wallet_dir,
    wallet_password=wallet_password
)

client = AIServiceVisionClient(config={}, signer=signer)

def handler(ctx: context.InvokeContext, data: io.BytesIO = None):
    logging.getLogger().info("Inside vision_client function")
    try:
        filename = parse_filename(headers=ctx.Headers())
        analyze_image_response = analyze_image(data)
        parsed_response = parse_analyze_result(analyze_image_response)
        if "true".__eq__(is_save):
            save_analyze_result(
                filename,
                parsed_response['bad_quality'],
                parsed_response['good_quality'],
                parsed_response['empty_background'],
                max(parsed_response,key=parsed_response.get)
            )
        else:
            logging.getLogger().debug("do nothing.")
        return response.Response(
            ctx=ctx,
            response_data=json.dumps(
                {
                    "result": max(parsed_response,key=parsed_response.get),
                    "confidence": max(parsed_response.values())
                }
            ),
            headers={"Content-Type": "application/json"}
        )
    except (Exception, ValueError) as ex:
        logging.getLogger().info(f'error parsing json payload: {str(ex)}')


def parse_filename(headers: dict):
    content_disposition = headers['content-disposition']
    splited_disposition = content_disposition.replace(' ', '').split(';')[2]
    return splited_disposition[10:len(splited_disposition) - 1]
    

def analyze_image(data: io.BytesIO):
    response = client.analyze_image(
        analyze_image_details=AnalyzeImageDetails(
            features=[
                ImageClassificationFeature(
                    feature_type='IMAGE_CLASSIFICATION',
                    model_id=model_id
                )
            ],
            image=InlineImageDetails(
                source="INLINE",
                data=base64.b64encode(data.read()).decode('utf-8')
            ),
            compartment_id=compartment_id
        )
    )
    return response.data


def parse_analyze_result(analyze_result):
    logging.getLogger().info("Inside parse_analyze_result")
    labels = analyze_result.labels
    result = {}
    for label in labels:
        match label.name:
            case "good_quality":
                result['good_quality'] = label.confidence
            case "bad_quality":
                result['bad_quality'] = label.confidence
            case "empty_background":
                result['empty_background'] = label.confidence
    return result

     
def save_analyze_result(filename, bad_quality, good_quality, empty_background, result):
    logging.getLogger().info("Inside save_analyze_result")
    row = (filename, bad_quality, good_quality, empty_background, result)
    with conn.cursor() as cursor:
        try:
            statement = """
                INSERT INTO RESULTS (
                    IMAGE_NAME,
                    BAD_QUALITY,
                    GOOD_QUALITY,
                    EMPTY_BACKGROUND,
                    RESULT
                ) VALUES (
                    :1,
                    :2,
                    :3,
                    :4,
                    :5
                )
            """
            cursor.execute(statement, row)
            conn.commit()
        except oracledb.Error as e:
            error, = e.args
            logging.getLogger().error(error.message)
            if (error.offset):
                logging.getLogger().error('^'.rjust(error.offset+1, ' '))

##### for debug.
def check_result():
    logging.getLogger().info("Inside check_result")
    with conn.cursor() as cursor:
        try:
            sql = """SELECT * FROM RESULTS"""
            for row in cursor.execute(sql):
                logging.getLogger().info(row)
        except oracledb.Error as e:
            error, = e.args
            logging.getLogger().error(error.message)
            logging.getLogger().error(sql)
            if (error.offset):
                logging.getLogger().error('^'.rjust(error.offset+1, ' '))


def delete_all_rows():
    logging.getLogger().info("Inside delete_all_rows")
    with conn.cursor() as cursor:
        try:
            cursor.execute("DELETE FROM RESULTS")
            conn.commit()
        except oracledb.Error as e:
            error, = e.args
            logging.getLogger().error(error.message)
            if (error.offset):
                logging.getLogger().error('^'.rjust(error.offset+1, ' '))

def main():
    filename="empty_background_66.jpg"
    with open(f"/home/shukawam/work/ai-bbs-vision/lemon_dataset/test/{filename}", "rb") as image:
        name = "debug"
        ctx = context.InvokeContext(
            app_id=name,
            app_name=name,
            fn_id=name,
            fn_name=name,
            call_id=name,
            headers={
                'content-type': 'multipart/form-data; boundary=ce560532019a77d83195f9e9873e16a1',
                'content-disposition': f'form-data; name="file"; filename="{filename}"'
            }
        )
        handler(ctx, image)
        check_result()
        # delete_all_rows()


if __name__ == '__main__':
    main()

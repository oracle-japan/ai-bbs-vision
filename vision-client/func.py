import io
import json
import logging
import base64
import os
import oracledb
from fdk import response, context
from oci.auth.signers import InstancePrincipalsSecurityTokenSigner, get_resource_principals_signer
from oci.ai_vision import AIServiceVisionClient
from oci.ai_vision.models import AnalyzeImageDetails, ImageClassificationFeature, InlineImageDetails

# from Functions Config
compartment_id = os.getenv('COMPARTMENT_ID')
model_id = os.getenv('MODEL_ID')
username = os.getenv('USERNAME')
dsn = os.getenv('DSN')
password = os.getenv('PASSWORD')

conn = oracledb.connect(
    user=username,
    password=password,
    dsn=dsn
)

is_local = os.getenv('IS_LOCAL')
if "true".__eq__(is_local):
    signer = InstancePrincipalsSecurityTokenSigner()
else:
    signer = get_resource_principals_signer()

client = AIServiceVisionClient(config={}, signer=signer)

def handler(ctx: context.InvokeContext, data: io.BytesIO = None):
    logging.getLogger().info("Inside vision_client function")
    try:
        filename = parse_filename(headers=ctx.Headers())
        resp = analyze_image(data)
        parsed_response = parse_analyze_result(resp)
        if "true".__eq__(is_local):
            logging.getLogger().debug("do nothing.")
        else:
            save_analyze_result(
                filename,
                parsed_response['bad_quality'],
                parsed_response['good_quality'],
                parsed_response['empty_background']
            )
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

     
def save_analyze_result(filename, bad_quality, good_quality, empty_background):
    logging.getLogger().info("Inside save_analyze_result")
    row = (filename, bad_quality, good_quality, empty_background)
    with conn.cursor() as cursor:
        try:
            statement = """
                INSERT INTO RESULTS (
                    IMAGE_NAME,
                    BAD_QUALITY,
                    GOOD_QUALITY,
                    EMPTY_BACKGROUND
                ) VALUES (
                    :1,
                    :2,
                    :3,
                    :4
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
    with open("/home/shukawam/work/ai-bbs-vision/lemon_dataset/test/good_quality_44.jpg", "rb") as image:
        # name = "debug"
        # ctx = context.InvokeContext(
        #     app_id=name,
        #     app_name=name,
        #     fn_id=name,
        #     fn_name=name,
        #     call_id=name,
        #     headers={
        #         'Content-Type': 'multipart/form-data; boundary=ce560532019a77d83195f9e9873e16a1',
        #         'Content-Disposition': 'form-data; name="file"; filename="good_quality_44.jpg"'
        #     }
        # )
        # handler(ctx, image)
        check_result()
        # delete_all_rows()


if __name__ == '__main__':
    main()

# import json
# import pytest
# from ocr-textract-app.app import lambda_handler

# @pytest.fixture()
# def apigw_event():
#     """ Generates API GW Event"""

#     return {
#         "body": json.dumps({
#             "file": "base64-encoded-file-content",
#             "file_name": "test.pdf"
#         })
#     }

# def test_lambda_handler(apigw_event):
#     ret = lambda_handler(apigw_event, "")
#     assert ret['statusCode'] == 200
#     assert 'Text extraction completed successfully' in ret['body']

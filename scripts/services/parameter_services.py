import os

import openpyxl

from fastapi import APIRouter, Depends, UploadFile, File
from scripts.config.description import Description
from scripts.constants.app_constants import AutomationConstants, Secrets
from scripts.core.handlers.parameter_handler import AppHandler
from scripts.logging.logger import logger
from scripts.utils.security_utils.security import verify_cookie

ut_app_router = APIRouter()
UPLOAD_DIR = "assets"


# ----------------------------------------------------------------------------------------------------------------------


@ut_app_router.post("/update_parameter", tags=["Automation"],
                    description=Description.app_services_des)
async def update_parameter(login_token: dict = Depends(verify_cookie), file: UploadFile = File(...)):
    """
    :param file:
    :param encrypt_payload:
    :param login_token:
    :return:
    """
    response_messages = ''
    try:
        file_content = await file.read()
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        print("file_path", file_path)
        with open(file_path, "wb") as f:
            f.write(file_content)
        encrypt_payload = AutomationConstants.encrypt_payload
        app_handler = AppHandler(login_token=login_token, encrypt_payload=encrypt_payload,
                                 file_path=file_path)
        response_messages = app_handler.automate_parameter()
        # return {'logs': [each for each in response_messages.strip().split('\n')]}
        return "done"
    except Exception as e:
        logger.exception(f"exception from generate form json logic {e}")
        return {'logs': [each for each in response_messages.strip().split('\n')]}

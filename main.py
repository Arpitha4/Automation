import os

from scripts.constants.app_constants import AutomationConstants
from scripts.core.handlers.parameter_category import ParameterCategoryHandler
from scripts.core.handlers.parameter_creation import ParameterCreationHandler
from scripts.core.handlers.parameter_groups import ParameterGroups
from scripts.logging.logger import logger

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'parameter_template')


def create_parameter(file_path: str, login_token: dict):
    try:
        with open(file_path, "rb") as f:
            file_content = f.read()

        upload_file_path = os.path.join(UPLOAD_DIR, os.path.basename(file_path))
        with open(upload_file_path, "wb") as f:
            f.write(file_content)

        encrypt_payload = AutomationConstants.encrypt_payload
        parameter_category = ParameterCategoryHandler(login_token=login_token, encrypt_payload=encrypt_payload,
                                                      file_path=upload_file_path)
        response = parameter_category.automate_parameter_category()
        print(f"Response from automate_parameter_category: {response}")

        parameter_groups = ParameterGroups(login_token=login_token, encrypt_payload=encrypt_payload,
                                           file_path=upload_file_path)
        response = parameter_groups.automate_parameter_groups()
        print(f"Response from automate_parameter_groups: {response}")

        parameter_creation = ParameterCreationHandler(login_token=login_token, encrypt_payload=encrypt_payload,
                                                      file_path=upload_file_path)
        response = parameter_creation.automate_parameter_creation()
        print(f"Response from automate_parameter_creation: {response}")

    except Exception as e:
        logger.exception(f"Exception from generate form json logic {e}")
        return {'logs': [str(e)]}

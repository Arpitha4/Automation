import os
from main import create_parameter
from scripts.config.app_configurations import EnvironmentDetails
from scripts.logging.logger import logger

if __name__ == "__main__":
    try:
        login_token = {'login-token': EnvironmentDetails.access_token}
        UPLOAD_DIR = os.path.join(os.path.dirname(__file__), 'parameter_template')
        file_path = os.path.join(UPLOAD_DIR, 'template1.xlsx')
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        create_parameter(file_path, login_token)
    except FileNotFoundError as fnf_error:
        logger.exception(f"FileNotFoundError: {fnf_error}")
    except Exception as e:
        logger.exception(f"Exception from generate form json logic: {e}")

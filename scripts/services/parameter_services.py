from scripts.constants.app_constants import AutomationConstants
from scripts.core.handlers.parameter_category import ParameterCategoryHandler
from scripts.core.handlers.parameter_creation import ParameterCreationHandler
from scripts.core.handlers.parameter_groups import ParameterGroups
from scripts.logging.logger import logger


class ParameterService:
    def __init__(self, login_token: dict):
        self.login_token = login_token
        self.responses = {}

    def process_parameters(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                file_content = f.read()

            with open(file_path, "wb") as f:
                f.write(file_content)

            self.responses['parameter_category'] = self._automate_parameter_category(file_path)
            self.responses['parameter_groups'] = self._automate_parameter_groups(file_path)
            self.responses['parameter_creation'] = self._automate_parameter_creation(file_path)

        except Exception as e:
            logger.exception(f"Exception from processing parameters: {e}")
            self.responses['error'] = str(e)

        return self.responses  # Return all responses, including any errors

    def _automate_parameter_category(self, upload_file_path: str):
        try:
            parameter_category = ParameterCategoryHandler(
                login_token=self.login_token,
                encrypt_payload=AutomationConstants.encrypt_payload,
                file_path=upload_file_path
            )
            response = parameter_category.automate_parameter_category()
            print(f"Response from automate_parameter_category: {response}")
            return response
        except Exception as e:
            logger.exception(f"Exception from automate_parameter_category: {e}")
            return {'error': str(e)}

    def _automate_parameter_groups(self, upload_file_path: str):
        try:
            parameter_groups = ParameterGroups(
                login_token=self.login_token,
                encrypt_payload=AutomationConstants.encrypt_payload,
                file_path=upload_file_path
            )
            response = parameter_groups.automate_parameter_groups()
            print(f"Response from automate_parameter_groups: {response}")
            return response
        except Exception as e:
            logger.exception(f"Exception from automate_parameter_groups: {e}")
            return {'error': str(e)}

    def _automate_parameter_creation(self, upload_file_path: str):
        try:
            parameter_creation = ParameterCreationHandler(
                login_token=self.login_token,
                encrypt_payload=AutomationConstants.encrypt_payload,
                file_path=upload_file_path
            )
            response = parameter_creation.automate_parameter_creation()
            print(f"Response from automate_parameter_creation: {response}")
            return response
        except Exception as e:
            logger.exception(f"Exception from automate_parameter_creation: {e}")
            return {'error': str(e)}

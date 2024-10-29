from scripts.constants.app_constants import AutomationConstants
from scripts.core.handlers.hierarchy_handler import HierarchyHandler
from scripts.core.handlers.parameter_category import ParameterCategoryHandler
from scripts.core.handlers.parameter_handler import ParameterCreationHandler
from scripts.core.handlers.parameter_groups import ParameterGroups
from scripts.core.handlers.unit_groups import UnitGroupsHandler
from scripts.core.handlers.units_handler import UnitsHandler
from scripts.logging.logger import logger
from scripts.core.handlers.industry_handler import IndustryHandler
from scripts.core.handlers.asset_model import AssetModelHandler


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

            handlers = [
                (UnitGroupsHandler, 'automate_unit_groups'),
                (UnitsHandler, 'automate_units'),
                (ParameterCategoryHandler, 'automate_parameter_category'),
                (ParameterGroups, 'automate_parameter_groups'),
                (ParameterCreationHandler, 'automate_parameter_creation'),
                # (HierarchyHandler, 'hierarchy_automation'),
                (IndustryHandler, 'automate_industry'),
                (AssetModelHandler, 'automate_asset_model')
            ]

            for handler_class, method in handlers:
                response, status = self._automate(handler_class, method, file_path)
                if not status:
                    return {'logs': [line for line in response.strip().split('\n')]}

        except Exception as e:
            logger.exception(f"Exception from processing parameters: {e}")
            self.responses['error'] = str(e)

        return self.responses

    def _automate(self, handler_class, method_name, upload_file_path):
        try:
            handler_instance = handler_class(
                login_token=self.login_token,
                encrypt_payload=AutomationConstants.encrypt_payload,
                file_path=upload_file_path
            )
            response = getattr(handler_instance, method_name)()
            if isinstance(response, str):
                print(f"Response from {method_name}:\n{response}")
            elif isinstance(response, tuple):
                formatted_response = '\n'.join([str(item) for item in response if item])
                print(f"Response from {method_name}:\n{formatted_response}")
            return (response, True) if not isinstance(response, tuple) else response
        except Exception as e:
            logger.exception(f"Exception from {method_name}: {e}")
            return str(e), False


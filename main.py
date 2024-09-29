import os
import logging
from scripts.config.app_configurations import EnvironmentDetails, TemplateDetails
from scripts.logging.logger import logger
from scripts.services.parameter_services import ParameterService

logging.basicConfig(level=logging.INFO)


class ParameterProcessor:
    """Class to handle parameter processing logic."""

    def __init__(self, login_token: dict):
        self.login_token = login_token
        self.upload_dir = os.path.join(os.path.dirname(__file__), TemplateDetails.FOLDER_NAME)
        self.file_path = os.path.join(self.upload_dir, TemplateDetails.FILE_NAME)

    def process(self):
        """Main method to execute parameter processing."""
        try:
            self.validate_file_path(self.file_path)
            parameter_service = ParameterService(self.login_token)
            responses = parameter_service.process_parameters(self.file_path)
            logger.info("Processing completed successfully. Responses: %s", responses)

        except FileNotFoundError as fnf_error:
            logger.exception("FileNotFoundError: %s", fnf_error)
        except Exception as e:
            logger.exception("An error occurred while processing parameters: %s", e)

    @staticmethod
    def validate_file_path(file_path: str):
        """Validate the existence of the file at the specified path."""
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")


def main():
    """Entry point for the processing logic."""
    try:
        login_token = {'login-token': EnvironmentDetails.access_token}
        processor = ParameterProcessor(login_token)
        processor.process()
    except Exception as e:
        logger.exception("An error occurred while initializing or processing the ParameterProcessor: %s", e)

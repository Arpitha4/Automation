import copy
import pandas as pd

import openpyxl
import requests
from fastapi import HTTPException, status

from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import BaseURLPaths
from scripts.constants.app_constants import Secrets, Parameter, AppConstants
from scripts.constants.parameter_constants import ParameterConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class AppHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None, response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages
        self.parameter_metadata = {}

    def automate_parameter(self):
        try:
            logger.info("Initiated parameter automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.metadata_sheet)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_parameter_data(merged_row_groups, df)
            self.convert_parameter_metadata_to_dict(df)

            self.update_parameter()

        except Exception as parameter_error:
            msg = f"Error while automating parameter: {parameter_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            return {}, self.response_messages, False

    def extract_parameter_data(self, merged_row_groups, df):
        try:
            group_dfs = []
            for each in merged_row_groups:
                group_df = df.iloc[each].reset_index(drop=True)
                group_df.dropna(how='all', inplace=True)
                group_df.dropna(how='all', axis=1, inplace=True)
                group_dfs.append(group_df)
            result_df = pd.concat(group_dfs, ignore_index=True)
            return result_df
        except Exception as extraction_error:
            msg = f"Error while extracting parameter data: {extraction_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def convert_parameter_metadata_to_dict(self, df):
        try:
            table_no_rows, table_no_columns = df.shape
            arr = df.to_numpy()
            keys = arr[1]
            metadata_list = []
            for row in range(2, table_no_rows):
                row_dict = {}
                for column in range(table_no_columns):
                    metadata_label = ParameterConstants.meta_data_mapping.get(keys[column].lower(), '')
                    metadata_value = arr[row][column]
                    if metadata_label:
                        row_dict[metadata_label] = metadata_value
                metadata_list.append(row_dict)
            self.parameter_metadata = metadata_list
        except Exception as metadata_error:
            msg = f"Error while converting parameter metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def update_parameter(self):
        try:
            payload_data = ParameterConstants.parameter_json
            print("data",payload_data)
        except Exception as metadata_error:
            msg = f"Error while updating the parameter data: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)


    def check_parameter_exits(self):
        try:
            # prepare payload
            payload = copy.deepcopy(Parameter.fetch_step_data_payload)

            # trigger fetch app data api
            url = f'{EnvironmentConstants.base_path}{BaseURLPaths.get_parameter_content}'

            # encode payload int jwt
            if self.encrypt_payload:
                payload = JWT().encode(payload=payload)
                response = requests.post(url, data=payload, headers=Secrets.headers, cookies=self.login_token)
            else:
                response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

            if response.status_code != 200:
                msg = "Failed to fetch parameter data\n"
                logger.error(msg)
                self.response_messages += msg
                raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=self.response_messages)

            # extract app data
            response = response.json()
            app_data = response.get('data', {})
            return app_data
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

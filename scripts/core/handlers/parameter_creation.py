import copy
import pandas as pd
import openpyxl
import requests

from fastapi import HTTPException, status

from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import ParametersAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.parameter_constants import ParameterConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class ParameterCreationHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None,
                 response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages
        self.parameter_metadata = dict()
        self.parameter_list = []

    def automate_parameter_creation(self):
        try:
            logger.info("Initiated parameter automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.parameter)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_parameter_data(merged_row_groups, df)
            self.convert_parameter_metadata_to_dict(df)

            _, parameter_data = self.check_parameter()

            get_data_type = self.get_data_type()

            if not parameter_data:
                self.create_parameter(parameter_data)
            else:
                msg = "Parameter exists"
                logger.info(msg)
                self.response_messages += msg

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
            if df.empty:
                raise ValueError("The input DataFrame is empty.")
            arr = df.to_numpy()
            keys = arr[1]
            if self.response_messages is None:
                self.response_messages = ""
            self.parameter_list = []
            for row in range(2, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = ParameterConstants.meta_data_mapping.get(keys[col].lower(), '')
                    #check
                    if metadata_label.lower() == 'tag_name':
                        if pd.isna(metadata_value[col]):
                            self.response_messages += 'Parameter is missing\n'
                            raise ValueError(self.response_messages)
                    if metadata_label:
                        value = metadata_value[col]
                        if isinstance(value, str):
                            value = value.strip()
                        elif pd.isna(value):
                            value = None
                        row_metadata[metadata_label] = value
                self.parameter_list.append(row_metadata)
        except Exception as metadata_error:
            msg = f"Error while converting parameter metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    # def create_parameter_category(self):
    #     try:
    #         payload_data = copy.deepcopy(ParameterConstants.parameter_category_json)
    #         for each_data in self.parameter_list:
    #             payload_data["tag_category_name"] = each_data.get('tag_category_name', '')
    #             payload_data["description"] = each_data.get('description', '')
    #             payload_data["tag_category_icon"] = each_data.get('tag_category_icon', '')
    #
    #             url = f'{EnvironmentConstants.base_path}{ParametersAPI.save_parameter_category}'
    #
    #             # encode payload into JWT
    #             if self.encrypt_payload:
    #                 payload = JWT().encode(payload=payload_data)
    #                 response = requests.post(url, data=payload, headers=Secrets.headers, cookies=self.login_token)
    #             else:
    #                 response = requests.post(url, json=payload_data, headers=Secrets.headers, cookies=self.login_token)
    #
    #             if response.status_code != 200:
    #                 msg = "Failed to fetch parameter data\n"
    #                 logger.error(msg)
    #                 self.response_messages += msg
    #                 raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=self.response_messages)
    #
    #     except Exception as metadata_error:
    #         msg = f"Error while updating the parameter data: {metadata_error}\n"
    #         logger.exception(msg)
    #         self.response_messages += msg
    #         raise ValueError(self.response_messages)

    def create_parameter(self, list_data):
        try:
            payload_data = copy.deepcopy(ParameterConstants.parameter_json)
            for each_data in self.parameter_list:
                payload_data["tag_name"] = each_data.get('tag_name', '')
                payload_data["description"] = each_data.get('description', '')
                # payload_data["category"] = list_data[0].get('value') if list_data else None
                url = f'{EnvironmentConstants.base_path}{ParametersAPI.save_parameter}'
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload_data)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload_data, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = "Failed to fetch parameter data\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)

        except Exception as metadata_error:
            msg = f"Error while updating the parameter data: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def check_parameter(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_content_json)
            filter_data_template = copy.deepcopy(ParameterConstants.parameter_filter_model)
            results = []

            for each_data in self.parameter_list:
                filter_data = filter_data_template.copy()
                filter_data['tag_name']['filter'] = each_data.get('tag_name', '').strip()
                payload['filters']['filterModel'] = filter_data

                url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_parameter_content}'
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = f"Failed to fetch parameter data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=self.response_messages)

                response_json = response.json()
                parameter_category_data = response_json.get('data', {}).get('bodyContent', [])
                if parameter_category_data:
                    results.append(parameter_category_data[0])

            return True, results
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

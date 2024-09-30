import copy
import pandas as pd
import openpyxl
import requests

from fastapi import HTTPException

from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import ParametersAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.parameter_constants import ParameterConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class ParameterGroups:
    def __init__(self, file_path, login_token=None, encrypt_payload=None,
                 response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages or ""
        self.parameter_metadata = dict()
        self.parameter_list = []

    def automate_parameter_groups(self):
        try:
            logger.info("Initiated parameter groups automation")

            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.parameter_groups)
            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_parameter_groups_data(merged_row_groups, df)
            self.convert_parameter_metadata_to_dict(df)

            _, parameter_groups_data = self.check_parameter_groups()
            parameter_categories_data = self.list_parameter_category()

            existing_tag_groups = {group["tag_group_name"].lower() for group in parameter_groups_data}
            new_tag_groups = {group["tag_group_name"].lower() for group in self.parameter_list}
            existing_categories = {category["label"].lower() for category in parameter_categories_data}
            new_categories = {category["category"].lower() for category in self.parameter_list if
                              category.get("category")}

            added_groups = new_tag_groups - existing_tag_groups
            removed_groups = existing_tag_groups - new_tag_groups
            added_categories = new_categories - existing_categories
            removed_categories = existing_categories - new_categories

            if added_groups or removed_groups:
                logger.info("Initiated update for Parameter Groups Information!!")

                if added_categories or removed_categories:
                    list_data = []
                    for each_parameter_id in parameter_categories_data:
                        if each_parameter_id["label"].lower() in new_categories:
                            list_data.append(each_parameter_id)
                    self.create_parameter_groups(list_data=list_data)
                    msg = f"Created Parameter Groups Information: {new_tag_groups} \n"
                    logger.info(msg)
                    self.response_messages += msg
            else:
                msg = f"Parameter Groups Information Exists: {existing_tag_groups} \n"
                logger.info(msg)
                self.response_messages += msg
            return self.response_messages
        except Exception as parameter_error:
            msg = f"Error while automating parameter groups: {parameter_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            return {}, self.response_messages, False

    def extract_parameter_groups_data(self, merged_row_groups, df):
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
            keys = arr[0]
            self.parameter_list = []
            for row in range(1, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = ParameterConstants.parameter_groups_meta_data.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'tag_group_name':
                        if pd.isna(metadata_value[col]):
                            self.response_messages += 'Parameter Groups is missing\n'
                            logger.error('Parameter Groups is missing in row: %s', row)
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

    def create_parameter_groups(self, list_data):
        try:
            payload_data = copy.deepcopy(ParameterConstants.parameter_groups_json)
            for each_data in self.parameter_list:
                payload_data.update({
                    "tag_group_name": each_data.get('tag_group_name', ''),
                    "description": each_data.get('description', '')
                })
            payload_data["category"] = list_data[0].get('value') if list_data else None
            url = f'{EnvironmentConstants.base_path}{ParametersAPI.save_parameter_groups}'
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

    def check_parameter_groups(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_content_json)
            filter_data_template = copy.deepcopy(ParameterConstants.parameter_groups_filter_model)
            results = []

            for each_data in self.parameter_list:
                filter_data = filter_data_template.copy()
                filter_data['tag_group_name']['filter'] = each_data.get('tag_group_name', '').strip()
                payload['filters']['filterModel'] = filter_data

                url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_parameter_group_content}'
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
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)

                response_json = response.json()
                parameter_groups_data = response_json.get('data', {}).get('bodyContent', [])
                if parameter_groups_data:
                    results.append(parameter_groups_data[0])

            return True, results
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def list_parameter_category(self):
        try:
            payload = copy.deepcopy(ParameterConstants.list_parameter_category)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.list_parameter_category}'
            if self.encrypt_payload:
                payload_encoded = JWT().encode(payload)
                response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                         cookies=self.login_token)
            else:
                response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

            if response.status_code != 200:
                msg = f"Failed to fetch parameter data. Status code: {response.status_code}, Response: {response.text}\n"
                logger.error(msg)
                self.response_messages += msg
                raise HTTPException(status_code=response.status_code, detail=self.response_messages)

            response_json = response.json()
            parameter_category_data = response_json["data"]
            if parameter_category_data:
                return parameter_category_data
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching parameter data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

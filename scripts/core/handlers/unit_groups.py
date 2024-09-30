import copy
import pandas as pd
import openpyxl
import requests
from fastapi import HTTPException
from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import UnitAPI
from scripts.constants.app_constants import Secrets, AppConstants
from scripts.constants.unit_constants import UnitConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.security_utils.jwt_util import JWT


class UnitGroupsHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None, response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages
        self.unit_metadata = dict()
        self.unit_list = []

    def automate_unit_groups(self):
        try:
            logger.info("Initiated Unit Group automation")
            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.unit_groups_sheet)

            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_unit_data(merged_row_groups, df)
            self.convert_unit_metadata_to_dict(df)

            _, unit_category_data = self.list_unit_group_exits()

            existing_unit_groups = [category["unit_group_name"].lower() for category in unit_category_data]
            new_unit_groups = [category["unit_group_name"].lower() for category in self.unit_list]

            added_groups = []
            removed_groups = []

            for new_group in new_unit_groups:
                if new_group not in existing_unit_groups:
                    added_groups.append(new_group)

            for existing_group in existing_unit_groups:
                if existing_group not in new_unit_groups:
                    removed_groups.append(existing_group)

            if added_groups or removed_groups:
                logger.info("Initiated update for units groups Information!!")
                self.create_unit()
                msg = f"Created unit groups Information: {new_unit_groups}\n"
                logger.info(msg)
                self.response_messages += msg
            else:
                msg = f"Unit groups Information Exists: {existing_unit_groups}\n"
                logger.info(msg)
                self.response_messages += msg
            return self.response_messages
        except Exception as parameter_error:
            msg = f"Error while automating unit: {parameter_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            return {}, self.response_messages, False

    def extract_unit_data(self, merged_row_groups, df):
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
            msg = f"Error while extracting unit data: {extraction_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def convert_unit_metadata_to_dict(self, df):
        try:
            if df.empty:
                raise ValueError("The input DataFrame is empty.")
            arr = df.to_numpy()
            keys = arr[0]
            if self.response_messages is None:
                self.response_messages = ""
            for row in range(1, len(arr)):
                metadata_value = arr[row]
                row_metadata = {}
                for col in range(len(keys)):
                    metadata_label = UnitConstants.unit_group_meta_data.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'unit_group_name':
                        if pd.isna(metadata_value[col]):
                            self.response_messages += 'Unit Group Name is missing\n'
                            raise ValueError(self.response_messages)
                    if metadata_label:
                        value = metadata_value[col]
                        if isinstance(value, str):
                            value = value.strip()
                        elif pd.isna(value):
                            value = None
                        row_metadata[metadata_label] = value
                self.unit_list.append(row_metadata)
        except Exception as metadata_error:
            msg = f"Error while converting unit metadata to dict: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def create_unit(self):
        try:
            payload_data = UnitConstants.unit_groups_payload
            for each_data in self.unit_list:

                payload_data["unit_group_name"] = each_data["unit_group_name"]
                payload_data["description"] = each_data["description"]
                url = f'{EnvironmentConstants.base_path}{UnitAPI.save_unit_groups}'

                # Encode payload into JWT
                if self.encrypt_payload:
                    payload = JWT().encode(payload=payload_data)
                    response = requests.post(url, data=payload, headers=Secrets.headers, cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload_data, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = "Failed to fetch unit data\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)
        except Exception as metadata_error:
            msg = f"Error while updating the unit data: {metadata_error}\n"
            logger.exception(msg)
            self.response_messages += msg
            raise ValueError(self.response_messages)

    def list_unit_group_exits(self):
        try:
            payload = copy.deepcopy(UnitConstants.unit_content_json)
            filter_data_template = copy.deepcopy(UnitConstants.unit_groups_filter_data)
            results = []

            for unit in self.unit_list:
                filter_data = filter_data_template.copy()
                filter_data["unit_group_name"]["filter"] = unit.get("unit_group_name", "").strip()
                payload["filters"]["filterModel"] = filter_data

                url = f'{EnvironmentConstants.base_path}{UnitAPI.list_unit_groups_data}'

                # Encode payload in JWT
                if self.encrypt_payload:
                    payload_encoded = JWT().encode(payload=payload)
                    response = requests.post(url, data=payload_encoded, headers=Secrets.headers,
                                             cookies=self.login_token)
                else:
                    response = requests.post(url, json=payload, headers=Secrets.headers, cookies=self.login_token)

                if response.status_code != 200:
                    msg = f"Failed to fetch unit group data. Status code: {response.status_code}, Response: {response.text}\n"
                    logger.error(msg)
                    self.response_messages += msg
                    raise HTTPException(status_code=response.status_code, detail=self.response_messages)

                response_json = response.json()
                unit_group_data = response_json.get('data', {}).get('bodyContent', [])
                if unit_group_data:
                    results.append(unit_group_data[0])
            return True, results
        except Exception as app_data_error:
            msg = f"Error while fetching unit data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)
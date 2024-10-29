import copy
import pandas as pd
import openpyxl
import requests
from fastapi import HTTPException
from scripts.constants import EnvironmentConstants
from scripts.constants.api_constants import UnitAPI, ParametersAPI
from scripts.constants.app_constants import AppConstants, Secrets
from scripts.constants.parameter_constants import ParameterConstants
from scripts.constants.unit_constants import UnitConstants
from scripts.logging.logger import logger
from scripts.utils.common_utils import CommonUtils
from scripts.utils.pagination_utils import PaginationUtils
from scripts.utils.security_utils.jwt_util import JWT


class UnitsHandler:
    def __init__(self, file_path, login_token=None, encrypt_payload=None, response_messages=None):
        self.login_token = login_token
        self.encrypt_payload = encrypt_payload
        self.file_path = file_path
        self.workbook = openpyxl.load_workbook(self.file_path, data_only=True)
        self.common_utils_obj = CommonUtils(workbook=self.workbook)
        self.response_messages = response_messages
        self.unit_metadata = dict()
        self.unit_list = []

    def automate_units(self):
        try:
            logger.info("Initiated Units automation")

            df, _, _ = self.common_utils_obj.convert_sheet_to_df(sheet_name=AppConstants.unit_sheet)
            merged_row_groups = self.common_utils_obj.group_merged_rows(df=df, merge_column=0)

            df = self.extract_unit_data(merged_row_groups, df)
            self.convert_unit_metadata_to_dict(df)

            _, unit_data = self.check_unit()
            unit_groups_data = self.list_unit_group()

            existing_unit = {group["label"].lower() for group in unit_data}
            new_unit = {group["name"].lower() for group in self.unit_list}
            existing_unit_group = {category["unit_group_name"].lower() for category in unit_groups_data[1]}
            new_unit_group = {category["unit_group_name"].lower() for category in self.unit_list if
                              category.get("unit_group_name")}

            # added_groups = new_unit_group - existing_unit_group
            removed_groups = existing_unit_group - new_unit_group
            added_unit = new_unit - existing_unit
            # removed_units = existing_unit - new_unit

            if removed_groups:
                logger.info("Initiated update for Units Information!!")

                if added_unit:
                    created_units = set()

                    for each_unit in unit_groups_data[1]:
                        for each_input_data in self.unit_list:
                            if each_unit["unit_group_name"] == each_input_data["unit_group_name"]:
                                self.create_unit(each_parameter_id=each_unit, input_data=each_input_data)
                                created_units.add(f"{new_unit}")

                    if created_units:
                        msg = f"Created Units: {', '.join(created_units)}"
                        logger.info(msg)
                        self.response_messages += msg + "\n"
                else:
                    msg = f"Units Information Exists: {existing_unit}\n"
                    logger.info(msg)
                    self.response_messages += msg
            else:
                msg = f"Unit groups Information not Exists: {existing_unit}\n"
                logger.info(msg)
                self.response_messages += msg
            return self.response_messages
        except Exception as unit_error:
            msg = f"Error while automating unit: {unit_error}\n"
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
                    metadata_label = UnitConstants.units_meta_data.get(keys[col].lower(), '')
                    if metadata_label.lower() == 'name':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Unit Name is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label.lower() == 'notation':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Unit Notation is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
                            raise ValueError(self.response_messages)
                    if metadata_label.lower() == 'unit_group_name':
                        if pd.isna(metadata_value[col]) or metadata_value[col].strip() == "":
                            error_message = f"Unit Group Name is missing in row number {row + 1}.\n"
                            self.response_messages += error_message
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

    def create_unit(self, each_parameter_id, input_data):
        try:
            payload_data = UnitConstants.units_payload

            payload_data["name"] = input_data["name"]
            payload_data["notation"] = input_data["notation"]
            payload_data["unit_group_name"] = input_data["unit_group_name"]

            payload_data["unit_group_id"] = each_parameter_id["id"]

            url = f'{EnvironmentConstants.base_path}{UnitAPI.save_units}'

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

    def check_unit(self):
        try:
            payload = copy.deepcopy(ParameterConstants.parameter_payload)

            url = f'{EnvironmentConstants.base_path}{ParametersAPI.get_unit_data}'
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
            data_type = response_json.get('data', {})
            if data_type:
                return True, data_type
            return False, {}
        except Exception as app_data_error:
            msg = f"Error while fetching unit data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

    def list_unit_group(self):
        try:
            url = f'{EnvironmentConstants.base_path}{UnitAPI.list_unit_groups_data}'
            payload = copy.deepcopy(UnitConstants.unit_content_json)

            results = PaginationUtils().pagination_function(url=url, payload=payload,
                                                            encrypt_payload=self.encrypt_payload,
                                                            login_token=self.login_token)
            return True, results if results else {}
        except Exception as app_data_error:
            msg = f"Error while fetching unit data: {app_data_error}\n"
            logger.exception(msg)
            raise ValueError(self.response_messages)

import secrets
import numpy as np
import pandas as pd
from scripts.logging.logger import logger

class CommonUtils:
    def __init__(self, workbook=None):
        self.workbook = workbook

    def convert_sheet_to_df(self, sheet_name, update_merge_cell=False):
        try:
            sheet = self.workbook[sheet_name]
            data = []
            for row in sheet.iter_rows(values_only=True):
                data.append(list(row))
            df = pd.DataFrame(data)

            sheet_data = np.empty(df.shape, dtype=object)

            self.extract_notes(sheet, sheet_data)

            df = pd.DataFrame(sheet_data)
            df = df.copy()
            df.dropna(how='all', inplace=True)
            df.dropna(how='all', inplace=True, axis=1)
            merged_cells = sheet.merged_cells.ranges

            # Iterate over merged cell ranges
            if update_merge_cell:
                self.update_merged_cell(merged_cells, sheet, df)
            return df, sheet, merged_cells
        except Exception as df_conversion_error:
            logger.error(df_conversion_error)

    def extract_notes(self, sheet, sheet_data):
        try:
            # Extract comments from the specified sheet
            for row in sheet.iter_rows():
                for cell in row:
                    _row = cell.row - 1
                    _col = cell.column - 1

                    _notes, _cell_value = self.extract_notes_and_cell_value(cell)

                    merged_data = None
                    if _cell_value and _notes:
                        merged_data = f'{_cell_value} <<<{_notes}>>>'
                    elif _cell_value:
                        merged_data = _cell_value
                    elif _notes:
                        merged_data = f'<<<{_notes}>>>'
                    if merged_data:
                        sheet_data[_row, _col] = merged_data
        except Exception as notes_extraction_error:
            logger.error(notes_extraction_error)
            raise notes_extraction_error

    def extract_notes_and_cell_value(self, cell):
        _notes, _cell_value = '', ''
        try:
            try:
                _notes = cell.comment.text
            except Exception as notes_error:
                msg = f'No notes configured: {notes_error}'


            try:
                _cell_value = cell.value
            except Exception as cell_value_error:
                msg = f'No values configured: {cell_value_error}'
        except Exception as extract_error:
            logger.error(extract_error)
        return _notes, _cell_value

    def update_merged_cell(self, merged_cells, sheet, df):
        try:
            for merged_cell in merged_cells:
                # Get the top-left cell of the merged range
                top_left_cell = sheet[merged_cell.min_row][merged_cell.min_col - 1]
                original_value = top_left_cell.value

                # Create a unique ID
                unique_id = str(secrets.token_hex(4))

                # Update the cell value with the unique ID concatenated to the existing value
                if original_value:
                    top_left_cell.value = f"{original_value} |{unique_id}|"

                # Update the DataFrame with the new value
                df.iat[merged_cell.min_row - 1, merged_cell.min_col - 1] = top_left_cell.value
        except Exception as update_error:
            logger.error(update_error)
            raise update_error

    def find_next_non_none_row(self, df, current_index):
        start_row, column = current_index
        # Create a boolean mask for non-None values in the specified column after the start_row
        mask = df.iloc[start_row + 1:, column].notna()
        # Find the index of the first True value in the mask
        next_non_none_row = mask.idxmax() if mask.any() else None
        return next_non_none_row

    def group_merged_rows(self, df, merge_column=0):
        try:
            groups = []
            current_group = []

            for i in range(len(df)):
                if pd.notna(df.iloc[i, merge_column]) and current_group:
                    groups.append(current_group)
                    current_group = []
                current_group.append(i)

            if current_group:
                groups.append(current_group)

            return groups
        except Exception as merge_error:
            logger.error(merge_error)
            raise merge_error


    # def fetch_project_template_data(self):
    #     try:
    #         payload = LogbookConstants.fetch_project_templates_payload
    #         final_params = urllib.parse.urlencode({'params': json.dumps(payload)})
    #
    #         # fetch project templates details
    #         url = f'{EnvironmentConstants.base_path}{UTCoreLogbooksAPI.fetch_templates}?{final_params}'
    #         response = requests.get(url, headers=Secrets.headers, cookies={'login-token': EnvironmentConstants.access_token})
    #
    #         if response.status_code != 200:
    #             return HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
    #                                  detail='Failed to fetch project templates data')
    #         response = response.json()
    #         return response.get('data', {})
    #     except Exception as trigger_error:
    #         logger.error(trigger_error)
    #         raise trigger_error
    #
    # def convert_hierarchy_data_to_enum(self):
    #     try:
    #         hierarchy_data = self.fetch_project_template_data()
    #         hierarchy_data = hierarchy_data.get('dropdown_data', [])
    #         hierarchy_data = {each['value']: each['label'] for each in hierarchy_data}
    #
    #         # Convert dictionary to Enum
    #         def enum_hierarchy_level(name, values):
    #             return Enum(name, {k: v for k, v in values.items()})
    #
    #         # Create Enum class
    #         HierarchyLevelEnum = enum_hierarchy_level('HierarchyLevelEnum', hierarchy_data)
    #         return HierarchyLevelEnum
    #     except Exception as enum_error:
    #         logger.error(enum_error)

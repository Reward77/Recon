import pandas as pd


class DataFrameService:

    @staticmethod
    def load_file(path: str):

        if path.lower().endswith(".csv"):

            return pd.read_csv(path)

        elif path.lower().endswith((".xlsx", ".xls")):

            return pd.read_excel(path)

        raise Exception("Unsupported file format.")
import pandas as pd


class HeaderService:

    @staticmethod
    def read_headers(path):

        if path.endswith(".csv"):

            df = pd.read_csv(
                path,
                nrows=0
            )

        else:

            df = pd.read_excel(
                path,
                nrows=0
            )

        return list(df.columns)
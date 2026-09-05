import pandas as pd


class NormalizationService:

    @staticmethod
    def normalize_columns(df):

        df.columns = [

            column.strip().lower().replace(" ", "_")

            for column in df.columns

        ]

        return df
    @staticmethod
    def normalize_strings(df):

        for column in df.select_dtypes(include="object"):

            df[column] = (

            df[column]

            .fillna("")

            .astype(str)

            .str.strip()

            )

        return df

    @staticmethod
    def normalize_dates(df):

        for column in df.columns:

             if "date" in column:

                df[column] = pd.to_datetime(

                df[column],

                errors="coerce"

                )

        return df

    @staticmethod
    def normalize_amounts(df):

        for column in df.columns:

            if "amount" in column:

                df[column] = (

                df[column]

                .astype(str)

                .str.replace(",", "", regex=False)

                .str.replace("₦", "", regex=False)

                .str.replace("$", "", regex=False)

                )

                df[column] = pd.to_numeric(

                    df[column],

                    errors="coerce"

                )

        return df

    @staticmethod
    def normalize_status(df):

        if "status" not in df.columns:

            return df

        mapping = {

            "successful": "SUCCESS",

            "success": "SUCCESS",

            "paid": "SUCCESS",

            "completed": "SUCCESS",

            "failed": "FAILED",

            "failure": "FAILED",

            "declined": "FAILED",

            "pending": "PENDING"

             }

        df["status"] = (

        df["status"]

        .astype(str)

        .str.lower()

        .map(mapping)

        .fillna("UNKNOWN")

        )

        return df

    @staticmethod
    def remove_duplicates(df):

        if "transaction_id" not in df.columns:
            return df

        return df.drop_duplicates(subset=["transaction_id"], keep="first")

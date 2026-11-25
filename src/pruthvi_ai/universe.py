import pandas as pd

NSE_CONSTITUENTS_URL = (
    "https://nsearchives.nseindia.com/"
    "content/indices/ind_nifty50list.csv"
)


def get_nifty50():
    try:
        df = pd.read_csv(NSE_CONSTITUENTS_URL)

        df.columns = df.columns.str.strip()

        required = {"Symbol", "Company Name"}

        if not required.issubset(set(df.columns)):
            raise ValueError("Unexpected NSE CSV format")

        df = df[["Symbol", "Company Name"]].copy()

        df["Symbol"] = df["Symbol"].astype(str).str.strip()
        df["Company Name"] = (
            df["Company Name"].astype(str).str.strip()
        )

        df = df.drop_duplicates(subset=["Symbol"])

        if len(df) != 50:
            raise ValueError(
                f"Expected 50 stocks, received {len(df)}"
            )

        if df.isnull().any().any():
            raise ValueError("Missing company information")

        return df.to_dict(orient="records")

    except Exception as error:
        raise RuntimeError(
            f"NIFTY 50 data unavailable: {error}"
        ) from error
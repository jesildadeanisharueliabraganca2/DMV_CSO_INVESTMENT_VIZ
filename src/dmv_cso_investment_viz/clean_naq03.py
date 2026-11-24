from common import *

GDP_KEYWORDS = ["gross domestic product", "gdp"]
GNP_KEYWORDS = ["gross national product", "gnp"]

def filter_gdp_gnp(row, dims):
    # check if any row has gdp or gnp keywords 
    combined_text = " ".join([str(row[dim]) for dim in ["statistic"] + dims])
    if has_any(combined_text, GNP_KEYWORDS):
        return "GNP"
    elif has_any(combined_text, GDP_KEYWORDS):
        return "GDP"
    else:
        return "OTHER"

def drop_other_rows(df):
    # keep the other rows in the cleaned_log file 
    dropped_rows = df.loc[df["TAG"] == "OTHER", "statistic"].unique()
    if len(dropped_rows):
        log(f"NAQ3: Dropped {list(dropped_rows)} rows with TAG 'OTHER':")
        
    # drop rows where TAG is OTHER
    return df[df["TAG"] != "OTHER"].copy()

def clean_naq03(local_dir=None):
    # naq3 data -> loading - tidy - inspect - keeping gdp & gnp
    raw_data = load("NAQ03", local_dir)
    df, dims=clean_raw_data(raw_data, "NAQ03")
    inspect_clean_data(df, dims, "NAQ03")

    # keep only unadjusted rows so we match to NAQ10
    dataframe = keep_one_adjustment(df, dims)

    # filter for gdp and gnp rows only
    dataframe["TAG"] = dataframe.apply(lambda row: filter_gdp_gnp(row, dims), axis=1)

    # drop rows where TAG is OTHER
    dataframe = drop_other_rows(dataframe)

    # Ensure price_basis column exists before selecting output columns
    if "price_basis" not in dataframe.columns:
        dataframe["price_basis"] = dataframe["statistic"].map(price_basis)

    # return cleaned dataframe with only the columns needed for merging and charting
    keep_columns = ["quarter", "price_basis", "statistic", "TAG", "value"]

    if "unit" in dataframe.columns:
        keep_columns.append("unit")

    return dataframe[keep_columns].sort_values(["price_basis", "TAG", "quarter"]).reset_index(drop=True)

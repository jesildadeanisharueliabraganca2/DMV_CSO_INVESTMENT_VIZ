from common import *

def reshape_naq10(naq10):
    # reshape the NAQ10 data to have one row per asset group and quarter
    reshaped = naq10.pivot_table(
        index=["quarter", "price_basis"], 
        columns="asset_group", 
        values="value"
        ).reset_index()
    reshaped.columns.name = None  # remove the name of the columns index

    reshaped.columns = [c.lower() for c in reshaped.columns]  # convert column names to lowercase
    reshaped["total_invest"] = reshaped["tangible"] + reshaped["intangible"]
    reshaped["tangible_share"] = (reshaped["tangible"] / reshaped["total_invest"]) * 100
    reshaped["intangible_share"] = (reshaped["intangible"] / reshaped["total_invest"]) * 100

    return reshaped

def reshape_naq3(naq3):
    # reshape the NAQ3 data to have one row per TAG and quarter
    reshaped = naq3.pivot_table(
        index=["quarter", "price_basis"], 
        columns="TAG", 
        values="value"
        ).reset_index()
    reshaped.columns.name = None  # remove the name of the columns index

    reshaped["gap_between_gdp_gnp"] = reshaped["GDP"] - reshaped["GNP"]

    return reshaped

def build_chart_data(naq10, naq3):
    # Inner join the reshaped NAQ10 and NAQ3 data on quarter and price_basis
    reshaped_naq10 = reshape_naq10(naq10)
    reshaped_naq3 = reshape_naq3(naq3)

    merged_chart_data = pd.merge(
        reshaped_naq10,
        reshaped_naq3,
        on=["quarter", "price_basis"],
        how="inner"
    )

    # calculate matrix of intangible_share as gdp & gnp
    merged_chart_data["intangible_gdp_share"] = (merged_chart_data["intangible"] / merged_chart_data["GDP"]) * 100
    merged_chart_data["intangible_gnp_share"] = (merged_chart_data["intangible"] / merged_chart_data["GNP"]) * 100

    return merged_chart_data.sort_values(["price_basis", "quarter"]).reset_index(drop=True)
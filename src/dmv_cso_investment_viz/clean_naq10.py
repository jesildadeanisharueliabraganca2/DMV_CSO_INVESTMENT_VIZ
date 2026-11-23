from common import *

#forming one variavle for tangible and intnagible keywords
ALL_ASSET_WORDS= INTANGIBLE_KEYWORDS+ TANGIBLE_KEYWORDS
#defining the final columns to be used in output
FINAL_OUTPUT_COLUMNS=["quarter","price_basis","statistic","asset","asset_group","is_aggregate","value"]

#function to cehck which of teh columns have the asset types
def guess_asset_dim(data,dimension_cols):
    best_column,best_hits=None,-1
    for col in dimension_cols:
        #calculate the hits
        hits=sum(has_any(str(v),ALL_ASSET_WORDS) for v in data[col])
        if hits> best_hits:
            best_column,best_hits=col,hits
    #return the best column
    return best_column

# cehcks for the three main keywords and returns the respective laels
def label_asset(asset_name):
    if has_any(asset_name,AGGREGATE_KEYWORDS):
        return "Aggregate"
    if has_any(asset_name,INTANGIBLE_KEYWORDS):
            return "Intangible"
    if has_any(asset_name,TANGIBLE_KEYWORDS):
            return "Tangible"
    return "UNCLASSIFIED"

#checks which group eacha sset was put in
def show_mapping(data):
    pairs=data[["asset","asset_group"]].drop_duplicates().sort_values(["asset","asset_group"])
    log("NAQ10 asset mapping")
    for asset, grp in pairs.itertuples(index=False):
         log(f"{grp}: {asset}")
    missed=pairs.loc[pairs["asset_group"]=="UNCLASSIFIED","asset"].tolist()
    if missed:
         log(f" No amtch for the {missed}")
#load and clean naq10 table    
def prepare_naq10(local_dir=None):
     #load the table from a saved csv. If not given , downlaod via teh CSO API
     raw_data=load("NAQ10",local_dir)
     #clean and give the list of dimenion columns
     data,dimemsion_cols=clean_raw_data(raw_data,"NAQ10")
     inspect_clean_data(data,dimemsion_cols,"NAQ10")
     data=keep_one_adjustment(data,dimemsion_cols)
     #cehck which column has asset name and call it asset

     asset_dimensions=guess_asset_dim(data,dimemsion_cols)
     log(f" NAQ10 using {asset_dimensions} as the asset colums")
     #tag each row and log the mapping
     data=data.rename(columns={asset_dimensions:"asset"})
     data["asset_group"]=data["asset"].apply(label_asset)
     show_mapping(data)

#keep only final columns which were listed above
     cols=FINAL_OUTPUT_COLUMNS+(["unit"] if "unit" in data.columns else [])
     return data[cols].sort_values(['price_basis',"asset","quarter"])


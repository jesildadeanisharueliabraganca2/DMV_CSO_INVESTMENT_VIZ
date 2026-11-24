import argparse
import re
import sys
from pathlib import Path
import pandas as pd
#the link for downloading the data using the REST API provided by CSO
API= "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{code}/CSV/1.0/en"



#lowercase substrings to classify rows into groups
#keywords for intangible label
INTANGIBLE_KEYWORDS=["intellectual property","research and development","r&d","software","databases","computer software"]
#keywords for tangible label

TANGIBLE_KEYWORDS=["dwelling", "building","construction","transport equipment","machinery","equipment","cultivated","aircraft"]

#Totals and subtotals left out so its not counted twice

AGGREGATE_KEYWORDS=["total","all asset","of which","gross fixed capital formation","(n11mg)"]
#keywords for current and constant
CURRENT_KEYWORDS=["current"]
CONSTANT_KEYWORDS=["constant","chain","volume"]
#all logs in one array
log_lines=[] 

#logging messages
def log(msg=""):
    print(msg)
    log_lines.append(str(msg))

#this is a helper function for check if a text constains any keywords
def has_any(text,keywords):
    t=str(text).lower()
    return any(k in t for k in keywords)

#this function is used to label according to constant and current keywords
def price_basis(stat):
    if has_any(stat,CONSTANT_KEYWORDS):
        return "constant"
    if has_any(stat,CURRENT_KEYWORDS):
        return "current"
    return "UNCLASSIFIED"

#load the table from a saved csv. If not given , downlaod via teh CSO API
def load(code,local_dir=None):
   #checks if local directory is True
    if local_dir:
        path=Path(local_dir)/f"{code}.csv"
        log(f"loading {code} from {path}")
        df=pd.read_csv(path,encoding="utf-8-sig")
    #else will use the API to get teh data
    else:
        url=API.format(code=code)
        log(f"Downlaoding {code} from {url}")

        #read data into pandas csv 
        df=pd.read_csv(url,encoding="utf-8-sig")
        #make the directiory if not present for storing raw data
        Path("raw").mkdir(exist_ok=True)
        df.to_csv(Path("raw")/f"{code}.csv",index=False)
    #get columns of the df and remove whitespaces
    df.columns=df.columns.str.strip()
    log(f"Raw shape {df.shape}")
    #return the dataframe
    return df

#getting the label of the code
def is_code_col(name):
    return bool(re.fullmatch(f"STATISTIC|TLIST.*|C\d+V\d+",name,re.IGNORECASE))

#cleaning the raw data
def clean_raw_data(df,code):
   
    cols=list(df.columns)
    #turning into lowercase
    lower=[c.lower() for c in cols]
    #enclosing in try and except blocks
    try:
        stat_col=cols[lower.index("statistic label")]
        value_col=cols[lower.index("value")]
        tlist_col=next(c for c in cols if c.upper().startswith("TLIST"))
    except(ValueError,StopIteration):
        sys.exit(f"{code}:unexpected columns {cols}. Check format")

    quarter_col=cols[cols.index(tlist_col)+1] #teh labels are right after the code
    unit_col=cols[lower.index("unit")] if "unit" in lower else None
    
    # Anything left that is noy a code col is a dimension
    used={stat_col,value_col,quarter_col,unit_col}
    #getting dimension columns
    dim_cols=[c for c in cols if c not in used and not is_code_col(c)]

    #renaming cols
    df=df.rename(columns={stat_col:"statistic",quarter_col:"quarter", value_col:"value", unit_col:"unit"})

    keep=["statistic","quarter"]+dim_cols+(["unit"] if unit_col else [])+ ["value"]
#filter df bey keep and make a copy
    df=df[keep].copy()

    df["quarter"]=pd.PeriodIndex(df["quarter"].astype(str).str.replace(" ",""), freq="Q").to_timestamp()

    #dropping nan
    df["value"]=pd.to_numeric(df["value"],errors="coerce")
    length_of_df=len(df)
    df=df.dropna(subset=["value"]).drop_duplicates() #drop duplicates
    log("Missing values and duplicated dropped")
#map the columns using the function
    df["prices_basis"]=df["statistic"].map(price_basis)

    return df,dim_cols

#inspecting the clean data
def inspect_clean_data(df,dim_cols,code):

    log(f"INSPECTION{code}")
    log("Statistics")

    for s,n in df["statistic"].value_counts().items():
        log(f"[{price_basis(s)}] {s} ({n} rows)")

    for col in dim_cols:
        log(f" {col}:{sorted(df[col].astype(str).unique())}")
    log(f"Quarter range: {df["quarter"].min().date()} to {df["quarter"].max().date()}")


#dropping seasonally adjusted rows if mixed
def keep_one_adjustment(df,dim_cols):
    for col in ["statistic"]+dim_cols:
        text=df[col].astype(str).str.lower()
        adjusted=text.str.contains("seasonally adjusted") & ~text.str.contains("unadjusted|not seasonally")

        if adjusted.any() and not adjusted.all():
            log(f"columns {col}: keeping unadjusted rows")
            df=df[~adjusted]

    return df

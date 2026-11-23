import argparse
import re
import sys
from pathlib import Path
import pandas as pd
#CSO PxStat API, {code} is replaced with table code
API= "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{code}/CSV/1.0/en"


# KEYWORD RULES
#lowercase substrings to classify rows
INTANGIBLE_KEYWORDS=["intellectual property","research and development","r&d","software","databases","computer software"]
TANGIBLE_KEYWORDS=["dwelling", "building","construction","transport equipment","machinery","equipment","cultivated","aircraft"]

#Totals and subtotals: excluded from shares to avoid double counting

AGGREGATE_KEYWORDS=["total","all asset","of which","gross fixed capital formation","(n11mg)"]

#Price basis; current proices vs chain-linked volumes
CURRENT_KEYWORDS=["current"]
CONSTANT_KEYWORDS=["constant","chain","volume"]
#all logs in one array
log_lines=[] 

def log(msg=""):
    """ Print a message and keep in log"""
    print(msg)
    log_lines.append(str(msg))


def has_any(text,keywords):
    """ True if any keyword appears in text"""
    t=str(text).lower()
    return any(k in t for k in keywords)


def load(code,local_dir=None):
    """ Load the CSO table from saved csv , if not available in saved csv download amd keep a raw copy"""
    if local_dir:
        path=Path(local_dir)/f"{code}.csv"
        log(f"loading {code} from {path}")
        df=pd.read_csv(path,encoding="utf-8-sig")
    else:
        url=API.format(code=code)
        log(f"Downlaoding {code} from {url}")
        df=pd.read_csv(url,encoding="utf-8-sig")
        Path("raw").mkdir(exist_ok=True)
        df.to_csv(Path("raw")/f"{code}.csv",index=False)
    df.columns=[ c.strip() for c in df.columns]
    log(f"Raw shape {df.shape}")
    return df


def tidy_pxstat(df,code):
    """ Turns a PxStat CSV into tidy columns"""
    cols=list(df.columns)
    #PxStat pairs each code column with a label colum
    stat_col=next((c for c in cols if c.lower()=="statistic label"),None)
    time_c=next((c for c in cols if c.upper().startswith("TLIST")),None)
    if stat_col is None or time_c is None:
        sys.exit(f"{code}:unexpected columns {cols}. Check format")

    time_col=cols[cols.index(time_c)+1]
    unit_col=next((c for c in cols if c.upper()=="UNIT"),None)
    value_col=next((c for c in cols if c.upper()=="VALUE"))
    # Code columns are dropped and labels are kept
    code_cols={c for c in cols if c=="STATISCTIC" or c.upper().startswith("TLIST") or re.fullmatch(r"C\d+V\d+",c)}
    dim_cols=[c for c in cols if c not in code_cols and c not in {stat_col,time_col,unit_col,value_col}]


    out=df[[stat_col,time_col]+ dim_cols+ ([unit_col] if unit_col else []) +[value_col]].copy()
    out=out.rename(columns={stat_col:"statistic",time_col:"quarter_raw", value_col:"value", **({unit_col:"unit"} if unit_col else{})})

    #Parse 1995Q1 into a adte 
    q=out["quarter_raw"].astype(str).str.replace(" ","",regex=False)
    out["quarter"]=pd.PeriodIndex(q,freq="Q").to_timestamp(how="start")
    #Missing values become NaN and are dropped
    before=len(out)
    out["value"]=pd.to_numeric(out["value"],errors="coerce")
    missing=out["value"].isna().sum()
    out=out.dropna(subset=["value"])
    log(f"Dropped {missing} rows")

    dupes=out.duplicated().sum()
    out=out.drop_duplicates()

    log(f"Dropped {dupes} duplicate rows")

    out["price_basis"]=out["statistic"].map(price_basis)
    return out.drop(columns="quarter_raw"),dim_cols




def price_basis(stat):
    """ Classify a statistic as current prices or constant"""
    if has_any(stat,CONSTANT_KEYWORDS):
        return "constant"
    if has_any(stat,CURRENT_KEYWORDS):
        return "current"
    return "UNCLASSIFIED"


def inspect(df,dim_cols,code):
    """ Log what the table contains, so the keyword rules can be checked"""

    log(f"INSPECTION{code}")
    log("Statistics")

    for s,n in df["statistic"].value_counts().items():
        log(f"[{price_basis(s)}] {s} ({n} rows)")

    for d in dim_cols:
        log(f"Values of '{d}':")
        for v in sorted (df[d].astype(str).unique()):
            log(f" {v} ")
    if "unit" in df:
        log(f"Units: {sorted(df['unit'].astype(str).unique())}")
    log(f"Quarter range: {df["quarter"].min().date()} to {df["quarter"].max().date()}")



def keep_one_adjustment(df,dim_cols):
    """ Keep unadjusted series only, so seasonal adjustment isn't mixed in"""
    sa_cols=[c for c in dim_cols if df[c].astype(str).str.lower().str.contains("season").any()]
    stat_sa=df["statistic"].str.lower().str.contains("seasonally adjusted")
    if stat_sa.any() and (~stat_sa).any():
        log("Both found ,keeping unadjusted")
        df=df[~stat_sa]
    for c in sa_cols:
        unadjusted=df[c].astype(str).str.lower().str.constains("unadjusted|not seasonally")
        if unadjusted.any():
            log(f"columns {c}: keeping uadjusted rows")
            df=df[unadjusted]
    return df

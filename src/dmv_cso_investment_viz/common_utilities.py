import argparse
import re
import sys
from pathlib import Path
import pandas as pd

API= "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{code}/CSV/1.0/en"


# KEYWORD RULES

INTANGIBLE_KEYWORDS=["intellectual property","research and development","r&d","software","databases","computer software"]
TANGIBLE_KEYWORDS=["dwelling", "building","construction","transport equipment","machinery","equipment","cultivated","aircraft"]

AGGREGATE_KEYWORDS=["total","all asset","of which","gross fixed capital formation","(n11mg)"]

CURRENT_KEYWORDS=["current"]
CONSTANT_KEYWORDS=["constant","chain","volume"]

log_lines=[]

def log(msg=""):
    print(msg)
    log_lines.append(str(msg))


def has_any(text,keywords):
    t=str(text).lower()
    return any(k in t for k in keywords)


def load(code,local_dir=None):
    if local_dir:
        path=Path(local_dir/f"{code}.csv")
        log(f"loading {code} from {path}")
        df=pd.read_csv(path,encoding="utf-8-sig")
    else:
        url=API.format(code=code)
        log(f"Downlaoding {code} from {url}")
        df=pd.read_csv(url,encoding="utf-8-sig")
        Path("raw").mkdir(exist_ok=True)
        df.to_csv(Path("raw")/f"{code}.csv",inex=False)
    df.columns=[ c.strip() for c in df.columns]
    log(f"Raw shape {df.shape}")
    return df




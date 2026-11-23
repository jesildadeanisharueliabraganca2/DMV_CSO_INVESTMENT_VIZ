import argparse
from pathlib import Path

import common 
from common import log
from clean_naq10 import clean_naq10
from clean_naq03 import clean_naq03
from merge import build_chart_data


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--local",help="folder containing NAQ10.csv and NAQ03.csv")
    args= ap.parse_args()

    naq10=clean_naq10(args.local)
    naq03=clean_naq03(args.local)

    if "unit" in naq10 and "unit" in naq03:
        u10,u03=set(naq10["unit"].astype(str)),set(naq03["unit"].astype(str))
        log(f"\n Units: NAQ10 {u10},NAQ03{u03}"+("" if u10==u03 else ":Check, units differ"))

    chart=build_chart_data(naq10,naq03)
    out=Path("clean")
    out.mkdir(exist_ok=True)
    naq10.to_csv(out/"naq10_clean.csv",index=False)
    naq03.to_csv(out/"naq03_clean.csv",index=False)
    chart.to_csv(out/ "merged_chart_data.csv",index=False)
    log("Saved clean files")




if __name__=="__main__":
    main()


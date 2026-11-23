import argparse
from pathlib import Path

import common 
from common import log
from clean_naq10 import clean_naq10
from clean_naq03 import clean_naq03
from merge import build_chart_data

OUTPUT_DIR=Path("clean")

#Reading the argumnets and returning the parsed argumnets
def read_args():
    par=argparse.ArgumentParser(description="Clean NAQ10/NAQ03")
    par.add_argument("--local",help="folder containing NAQ10.csv and NAQ03.csv")
    return par.parse_args()
# comparing the units of investments and macros
def compare_units(investment,other):
    if "unit" not in investment or "unit" not in other:
        return
    units_of_a=set(investment["unit"].astype(str))
    units_of_b=set(other["unit"].astype(str))
    msg=f"\n Units: NAQ10 {units_of_a} NAQ03 {units_of_b}"
    #checking if units are same or not
    if units_of_a!=units_of_b:
        msg+= ":Check units differ"

    log(msg)

#this function is for saving the file 
def save_all(investment,other,chart):
    OUTPUT_DIR.mkdir(exist_ok=True)
    files={
        "naq10_clean.csv":investment,
        "naq03_clean.csv":other,
        "merged_chart_data.csv":chart
    }

    for fn, fr in files.items():
        fr.to_csv(OUTPUT_DIR/fn,index=False)

    log("Saved clean files")


#main function for running all above defined fucntions
def main():
    #read arguments
    args= read_args()
    #clean naq10

    investment=clean_naq10(args.local)
    #clean naq03
    other=clean_naq03(args.local)
    #compare the two units
    compare_units(investment,other)
    #build the chart using the cleaned output
    chart=build_chart_data(investment,other)
    #save all 
    save_all(investment,other,chart)





if __name__=="__main__":
    main()


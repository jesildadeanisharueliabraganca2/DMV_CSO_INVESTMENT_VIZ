from common import *

def clean_naq10(local_dir=None):
    #Load,tidy,inspect and keep unadjusted series only
    raw=load("NAQ10",local_dir)
    df,dims=tidy_pxstat(raw,"NAQ10")
    inspect(df,dims,"NAQ10")
    df=keep_one_adjustment(df,dims)


#Asset column
    assest_col=max(dims,key=lambda c: df[c].astype(str).map(lambda v: has_any(v,INTANGIBLE_KEYWORDS+TANGIBLE_KEYWORDS)).sum())
    df=df.rename(columns={assest_col:"asset"})
    log(f"\n NAQ10 asset column detected")
    #Flag totals/subtotals so they are not counted twice
    df["is_aggregate"]=df["asset"].map(lambda a :has_any(a,AGGREGATE_KEYWORDS))


    def group(a):
        if has_any(a,INTANGIBLE_KEYWORDS):
            return "Intangible"
        if has_any(a,TANGIBLE_KEYWORDS):
            return "Tangible"
        return "UNCLASSIFIED"

    df["asset_group"]=df["asset"].map(group)
    df.loc[df["is_aggregate"],"asset_group"]="Aggregate"
    log(f"\n NAQ10 asset classification")


    for (a,g),_ in df.groupby(["asset","asset_group"]):
        log(f"{g:13s} : {a}")
    #Warn about assets no keyword matched

    unclassified=df.loc[df["asset_group"]=="UNCLASSIFIED","asset"].unique()
    if len(unclassified):
        log(f" Unclasified assets {list(unclassified)}")
    #Keep ony the columns the merge and chart need

    keep=["quarter","price_basis","statistic","asset","asset_group","is_aggregate","value"]
    keep+= [c for c in ["unit"] if c in df]
    return df[keep].sort_values(["price_basis","asset","quarter"])



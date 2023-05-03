"""
1. Update PA data: Data/Plenty/PREP2XL_v122_ICAS sec ..xlsm files
2. Remove cache: Data/Plenty/Q, P, 09, and 10.feather
3. Update bodemtemps_260.txt
4. Check the content of config_fn, e.g., number of wells etc.

"""

import os
from ..src.capaciteit_strang import get_config
import dawacotools as dw
import pandas as pd
import numpy as np
from datetime import timedelta
from data_functions import get_knmi_bodemtemperature
from data_functions import prepare_strang_data
from data_functions import read_plenty_excel

data_fd = os.path.join("..", "Data")
config_fn = "strang_props6.xlsx"
config = get_config(os.path.join(data_fd, config_fn))

bodemtemp_fn = os.path.join(data_fd, "bodemtemps_260.txt")
bodemtemp = get_knmi_bodemtemperature(bodemtemp_fn)

fp_in = os.path.join(data_fd, "Plenty", "PREP2XL_v122_ICAS sec Q")
fp_out = os.path.join(data_fd, "Plenty", "Q.feather")
prepare_strang_data(fp_in, fp_out, config)

fp_in = os.path.join(data_fd, "Plenty", "PREP2XL_v122_ICAS sec P")
fp_out = os.path.join(data_fd, "Plenty", "P.feather")
prepare_strang_data(fp_in, fp_out, config)

fp_in = os.path.join(data_fd, "Plenty", "PREP2XL_v122_IKIEF sec 09")
fp_out = os.path.join(data_fd, "Plenty", "09.feather")
prepare_strang_data(fp_in, fp_out, config)

fp_in = os.path.join(data_fd, "Plenty", "PREP2XL_v122_IKIEF sec 10")
fp_out = os.path.join(data_fd, "Plenty", "10.feather")
prepare_strang_data(fp_in, fp_out, config)

infil_temp = dw.get_daw_ts_temp(
    mpcode="19CZL5132", filternr=1
)  # See infiltration_temperature.py

pandpeil_fp = os.path.join(data_fd, "Plenty", "PREP2XL_v122_pandpeilen")
pandpeil = read_plenty_excel(pandpeil_fp)

for strang, c in config.iterrows():
    # if strang != "IK105":
    #     continue

    if "Q" in strang:
        fp_out = os.path.join(data_fd, "Plenty", "Q.feather")
    elif "P" in strang:
        fp_out = os.path.join(data_fd, "Plenty", "P.feather")
    elif "9" in strang:
        fp_out = os.path.join(data_fd, "Plenty", "09.feather")

    elif "10" in strang:
        fp_out = os.path.join(data_fd, "Plenty", "10.feather")

    df = prepare_strang_data("", fp_out, config)
    if "index" in df:  # in some datasets a column named index falsely appeared
        del df["index"]

    for key in filter(lambda k: "FT" in k, df.columns):
        ndt = int(timedelta(days=0.5) / (df.index[1] - df.index[0]))
        df[key] = df[key].interpolate("slinear", limit=ndt)
        df[key] = df[key].fillna(0)

    for key in filter(lambda k: "FQ" in k, df.columns):
        ndt = int(timedelta(days=0.5) / (df.index[1] - df.index[0]))
        df[key] = df[key].interpolate("slinear", limit=ndt)
        df[key] = df[key].fillna(0)

    df_out = pd.DataFrame(
        index=df.index,
        data={
            "Q": df.eval(c.PA_tag_flow),  # flow + spui m3/h
            "spui": 4 * df[f"{c.PA_tag_prefix}_FQ11R"],  # spui m3/h
            "P": df.eval(c.PA_tag_hleiding),  # mNAP
            "pandpeil": pandpeil.eval(c.PA_tag_pandpeil),  # mNAP
            "T_infil": np.interp(  # See infiltration_temperature.py
                df.index, infil_temp.index, infil_temp, left=np.nan, right=np.nan
            ),
            "T_bodem": np.interp(  # See infiltration_temperature.py
                df.index, bodemtemp.index, bodemtemp["TB3"], left=np.nan, right=np.nan
            ),
        },
    )

    nfilters = sum(f"gws_{c.Dawaco_tag}" in k for k in df)

    for i in range(nfilters):
        df_out[f"gws{i}"] = df[f"gws_{c.Dawaco_tag}_{i}"]
        df_out[f"gwt{i}"] = df[f"gwt_{c.Dawaco_tag}_{i}"]

    df_out.index.rename("Datum", inplace=True)
    df_out.reset_index().to_feather(
        os.path.join(data_fd, "Merged", f"{strang}.feather")
    )

print("hoi")

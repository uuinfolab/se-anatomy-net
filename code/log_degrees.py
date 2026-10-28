import os, glob, parse, pickle, sys, gc
import numpy as np
import pandas as pd
import random
import scipy.sparse
import scipy.sparse.csgraph
import math
import networkit as nk


## GLOBALS
csv_path="../results2"
log_path="../result_logs"
plot_path="../result_plots"
lisa_folder="../.."             ### NB: fill in path to LISA csv folder
lisa_prefix="mat_lev_lisa_"     ### NB: fill in prefix to LISA csv filename
obj_path=csv_path


# Read cmd args: mode [top] start_year end_year
args = sys.argv[1:]
if len(args) < 3:
    print("Usage: python log_degrees.py <mode> <start_year> <end_year>")
    print("       python log_degrees.py <mode> <top_layer> <start_year> <end_year>")
    sys.exit(1)

mode = args[0]
if len(args) == 4:
    top        = args[1]
    start_year = int(args[2])
    end_year   = int(args[3])
else:
    top        = ""
    start_year = int(args[1])
    end_year   = int(args[2])


layer_names_default = ["close_family","extended_family","household","neighbourhood","education","work"]

layer_short_map = {
    "close_family":    "close",
    "extended_family": "ext",
    "household":       "house",
    "education":       "edu",
    "neighbourhood":   "nbr",
    "work":            "work",
}


for year in range(start_year, end_year + 1):
    print(f"\n=== Processing year {year} | mode={mode} ===")

    lisa_path = f"{lisa_folder}/{lisa_prefix}{year}.csv"

    # Determine which layers to process this year
    layer_names = [top] if top != "" else layer_names_default

    node_df  = None
    lisa_df  = None

    if mode == "make-edge":
        print(f"Reading LISA dataframe for {year}")
        lisa_df      = pd.read_csv(lisa_path, index_col="LopNr", usecols=["LopNr","LopNr_CfarNr"], encoding='latin-1')
        lisa_members = list(lisa_df.index)

    for layer_name in layer_names:

        if mode == "make-edge":
            print(f"Reading {layer_name}.")
            df = (pd.read_csv(f"{csv_path}/{layer_name}{year}.csv")
                    [["PersonNr","PersonNr2"]]
                    .astype({"PersonNr":"int","PersonNr2":"int"}))

            print(f"{layer_name} size: {len(df.index)}")

            print(f"Dropping non-LISA members.")
            df = df.drop(
                df[~df["PersonNr"].isin(lisa_members) | ~df["PersonNr2"].isin(lisa_members)].index
            )

            print(df)

            print(f"Saving to csv & edgelist.")
            df.to_csv(f"{csv_path}/filtered_{layer_name}_{year}.csv")
            df.to_csv(f"{csv_path}/filtered_edgelist_{layer_name}_{year}.csv",
                      sep=" ", index=False, header=False)

        elif mode == "calc-degs":
            print(f"Reading {layer_name} from edgelist.")
            G = nk.readGraph(
                f"{csv_path}/filtered_edgelist_{layer_name}_{year}.csv",
                nk.Format.EdgeListSpaceOne
            )

            print(f"Calculating degrees, making dict.")
            degs     = []
            deg_dict = {}

            for u in G.iterNodes():
                if G.hasNode(u):
                    d_val = G.degree(u)
                    degs.append(d_val)
                    deg_dict[u + 1] = d_val
                else:
                    deg_dict[u + 1] = 0.0

            layer_short = layer_short_map.get(layer_name, layer_name)

            if layer_name == "close_family":
                node_df = pd.DataFrame.from_dict(deg_dict, orient="index",
                                                  columns=[f"deg_{layer_short}"])
            else:
                layer_df = pd.DataFrame.from_dict(deg_dict, orient="index",
                                                   columns=[f"deg_{layer_short}"])
                node_df  = node_df.merge(layer_df, how="outer",
                                         left_index=True, right_index=True)

    # Save per-year degree table
    if mode == "calc-degs" and node_df is not None:
        print(f"Saving node_df for {year}.")
        node_df.fillna(0.0)
        out_path = f"{log_path}/filtered_node_a_{year}.csv"
        node_df.to_csv(out_path)
        print(f"Saved: {out_path}")

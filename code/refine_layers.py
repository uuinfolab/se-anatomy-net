import os, glob, parse, pickle, sys, gc
import numpy as np
import pandas as pd

# Local imports
from simplify_family import read_in_network, simplify_family_layer, make_entire_edge_list

## GLOBALS
csv_path="../results2"
log_path="../result_logs"
plot_path="../result_plots"
obj_path=csv_path


# Read cmd args: mode [top] start_year end_year
args = sys.argv[1:]
if len(args) < 3:
    print("Usage: python refine_layers.py <mode> <start_year> <end_year>")
    print("       python refine_layers.py <mode> <top_layer> <start_year> <end_year>")
    sys.exit(1)

mode = args[0]
# Optional layer filter before years
if len(args) == 4:
    top        = args[1]
    start_year = int(args[2])
    end_year   = int(args[3])
else:
    top        = ""
    start_year = int(args[1])
    end_year   = int(args[2])


# Removes self-loops from the dataframe (assumes columns ["PersonNr","PersonNr2"])
def remove_self_loops(df):
    index_mask = df[(df["PersonNr"] == df["PersonNr2"])].index
    return df.drop(index_mask).reset_index(drop=True)


for year in range(start_year, end_year + 1):
    print(f"\n=== Processing year {year} | mode={mode} ===")

    if mode == "fix":
        print("Quick fix")
        df = pd.read_csv(f"{csv_path}/family{year}.csv")
        df = df[["PersonNr","PersonNr2"]].astype({"PersonNr":"int","PersonNr2":"int"})
        df.to_csv(f"{csv_path}/family{year}.csv")
        df.to_csv(f"{csv_path}/edgelist_family{year}.csv", sep=" ", index=False, header=False)

    elif mode == "fam":
        print("Reading full family network")
        fam_df = read_in_network(pd.read_csv(f"{csv_path}/final_network{year}.csv"), "PersonNr")
        print("Making edgelist")
        df = make_entire_edge_list(fam_df)
        print("Removing self loops")
        df = remove_self_loops(df)
        # Keep 'connection' column for sub-layer filtering; drop it only when saving
        df = df.astype({"PersonNr":"int","PersonNr2":"int"})
        df[["PersonNr","PersonNr2"]].to_csv(f"{csv_path}/family{year}.csv")
        df[["PersonNr","PersonNr2"]].to_csv(f"{csv_path}/edgelist_family{year}.csv", sep=" ", index=False, header=False)

        print("df:"); print(df)

        close_labels = ["parent","siblings","child","partners"]
        ext_labels   = ["grandparents","grandchildren","aunts_uncles","niece_nephews","cousins"]
        house_labels = ["family_household"]

        # Close family
        print("Make close family")
        close_mask = df["connection"].isin(close_labels)
        close_df = df[close_mask][["PersonNr","PersonNr2"]].astype({"PersonNr":"int","PersonNr2":"int"})
        close_df.to_csv(f"{csv_path}/close_family{year}.csv")
        close_df.to_csv(f"{csv_path}/edgelist_close_family{year}.csv", sep=" ", index=False, header=False)
        print("close df:"); print(close_df)

        # Extended family
        print("Make extended family")
        ext_mask = df["connection"].isin(ext_labels)
        ext_df = df[ext_mask][["PersonNr","PersonNr2"]].astype({"PersonNr":"int","PersonNr2":"int"})
        ext_df.to_csv(f"{csv_path}/extended_family{year}.csv")
        ext_df.to_csv(f"{csv_path}/edgelist_extended_family{year}.csv", sep=" ", index=False, header=False)
        print("extended df:"); print(ext_df)

        # Household
        print("Make household")
        house_mask = df["connection"].isin(house_labels)
        house_df = df[house_mask][["PersonNr","PersonNr2"]].astype({"PersonNr":"int","PersonNr2":"int"})
        house_df.to_csv(f"{csv_path}/household{year}.csv")
        house_df.to_csv(f"{csv_path}/edgelist_household{year}.csv", sep=" ", index=False, header=False)
        print("household df:"); print(house_df)

    elif mode == "nbr":
        print("Removing loops from neighbourhood")
        n_df = pd.read_csv(f"{csv_path}/old_neighbourhood{year}.csv").astype({"PersonNr":"int","PersonNr2":"int"})
        n_df = remove_self_loops(n_df)
        n_df.to_csv(f"{csv_path}/neighbourhood{year}.csv")
        n_df.to_csv(f"{csv_path}/edgelist_neighbourhood{year}.csv", sep=" ", index=False, header=False)

    elif mode == "edu":
        print("Removing loops from education")
        e_df = pd.read_csv(f"{csv_path}/old_education{year}.csv").astype({"PersonNr":"int","PersonNr2":"int"})
        e_df = remove_self_loops(e_df)
        e_df.to_csv(f"{csv_path}/education{year}.csv")
        e_df.to_csv(f"{csv_path}/edgelist_education{year}.csv", sep=" ", index=False, header=False)

    elif mode == "work":
        print("Removing loops from work")
        w_df = pd.read_csv(f"{csv_path}/old_work{year}.csv").astype({"PersonNr":"int","PersonNr2":"int"})
        w_df = remove_self_loops(w_df)
        w_df.to_csv(f"{csv_path}/work{year}.csv")
        w_df.to_csv(f"{csv_path}/edgelist_work{year}.csv", sep=" ", index=False, header=False)

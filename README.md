# Anatomy of a Swedish population-scale network

Material for constructing the multilayer population-scale network for the paper "Anatomy of a Swedish population-scale network". Link: <https://doi.org/10.1038/s41598-025-15966-x>

Builds six yearly edgelists from register data (close family, extended family, household, neighbourhood, education, work). Each is filtered to the people present in that year's LISA file.

## Requirements

**Python 3** with:

```
pip install pandas numpy scipy tqdm parse networkit
```

**Directory layout.** `refine_layers.py` and `log_degrees.py` use hard-coded relative paths, so run every command from the folder that holds the scripts. 
The expected LISA csv files can live anywhere: set `lisa_folder` and `lisa_prefix` at the top of `log_degrees.py` (see step 7). 
Using the default hard-coded paths, the expected folder layout is:

```
<root>/
├── mat_lev_lisa_XXXX.csv        # LISA csv, one file per year
└── <project>/
    ├── code/                    # all .py scripts: run everything from here
    └── results2/                # all layer outputs and final edgelists
```

**File lists.** Each layer script takes a plain-text file listing the raw LISA data it should read, one absolute path per line, in ascending year order. The year is counted from `<begin_year>` and goes up by one per line, so a missing year still needs its own line. For a single year, the list is one line, e.g.:

```
# lisa_files.txt
/path/to/raw/lisa_XXXX.csv
```


## Step by step (example for year 2017)

Run everything from `code/`:

```
cd <project>/code
```

### 1. Family layer

Example usage:
```
python family_layer.py ../family_out family_files.txt 2017 LopNr LopNr_FamId
```

Arguments: `<output_folder> <file_list> <begin_year> <personnr_var> <famid_var>`.

Output: `../family_out/family_layer2017/final_network2017.csv`, plus `.pkl` files.

> Parent and child links build up over the years in the file list. Each year reads the
> previous year's `.pkl` files. With only 2017 in the list, you get only the links
> visible in 2017 households. For more complete family links, start the list at an 
> earlier year, and run every year up to 2017 in one call.

### 2. Neighbourhood layer

Example usage:
```
python neighbourhood_layer.py LopNr <PROPERTY_VAR> <PROPERTY_VAR_2000> 2017 nbr_files.txt ../results2
```

Arguments: `<personnr_var> <property_var> <property_var_for_2000> <begin_year> <file_list> <output_folder>`.

Output: `../results2/neighbourhood2017.csv`

### 3. Education layer

Example usage:
```
python education_layer.py LopNr 2017 edu_files.txt ../results2
```

Arguments: `<personnr_var> <begin_year> <file_list> <output_folder>`

Output: `../results2/education2017.csv`

### 4. Work layer

Example usage:
```
python work2_layer.py work_files.txt 2017 ../results2
```

Arguments: `<file_list> <begin_year> <output_folder>`.

Output: `../results2/work2017.csv`


### 5. Rename and move

`refine_layers.py` expects specific names in `../results2`:

```
cp ../family_out/family_layer2017/final_network2017.csv ../results2/final_network2017.csv
mv ../results2/neighbourhood2017.csv ../results2/old_neighbourhood2017.csv
mv ../results2/education2017.csv     ../results2/old_education2017.csv
mv ../results2/work2017.csv          ../results2/old_work2017.csv
```

### 6. Refine: split family and remove self-loops

Example usage:
```
python refine_layers.py fam  2017 2017
python refine_layers.py nbr  2017 2017
python refine_layers.py edu  2017 2017
python refine_layers.py work 2017 2017
```

Arguments: `<mode> <start_year> <end_year>`. 

Outputs in `../results2`: `close_family2017.csv`, `extended_family2017.csv`,
`household2017.csv`, `neighbourhood2017.csv`, `education2017.csv`, `work2017.csv`.
Each also has an unfiltered `edgelist_*` version.

### 7. Filter to the 2017 LISA population

Example usage:
```
python log_degrees.py make-edge 2017 2017
```

This script reads `{lisa_folder}/{lisa_prefix}{year}.csv`, and drops every edge with an endpoint not in it.

Before running, set the two globals at the top of `log_degrees.py` to point at your LISA files:

```
lisa_folder = "../.."            # folder holding the yearly LISA CSVs
lisa_prefix = "mat_lev_lisa_"    # filename prefix; the year and .csv are appended
```

The script then reads `{lisa_folder}/{lisa_prefix}{year}.csv`, which is
`../../mat_lev_lisa_2017.csv` with the defaults.


### Result

The six final edgelists, in `../results2`. They are space-separated with no header.

```
filtered_edgelist_close_family_2017.csv
filtered_edgelist_extended_family_2017.csv
filtered_edgelist_household_2017.csv
filtered_edgelist_neighbourhood_2017.csv
filtered_edgelist_education_2017.csv
filtered_edgelist_work_2017.csv
```

## Notes

- Edges are directed and can appear more than once (A->B and B->A). Deduplicate them if
  you need a simple undirected graph.




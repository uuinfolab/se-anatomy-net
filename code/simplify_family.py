import ast
import pandas as pd

# -------------------------------------------------------------------------------------------------
# ------------------------------------- Helper function -------------------------------------------
# -------------------------------------------------------------------------------------------------

def convert_to_set(s):
    return ast.literal_eval(s) if pd.notna(s) else s

def combine_sets(row, variable):
    non_nan_sets = [s for col, s in row.items() if col != variable and isinstance(s, set) and pd.notna(s)]
    return set.union(*non_nan_sets) if non_nan_sets else None


# -------------------------------------------------------------------------------------------------
# ------------------------------------------ Functions --------------------------------------------
# -------------------------------------------------------------------------------------------------


def read_in_network(data, variable):
    """
    Helps correct the read in of the family layer. Run this before converting the family-layer into an edge list. 

    Parameters:
    - data: resulting dataframe of the family layer creation
    - variable: the variable name of the PersonNr (should always be PersonNr) (or not)

    Returns: 
    - corrected dataframe
    """
    data = data.rename(columns={data.columns[0]: variable})


    # Apply the conversion function to all columns except the first one
    for col in data.columns[1:]:
        data[col] = data[col].apply(convert_to_set)

    return data

def simplify_family_layer(data, variable):
    """
    Adds a column for All Family Connections. 

    Parameters:
    - data: resulting dataframe of the family layer creation
    - variable: the variable name of the PersonNr (should always be PersonNr) (or not)

    Returns: 
    - dataframe with a column collecting all relationships a person has
    """
    # Apply the combine_sets function to each row
    data['AllFamilyConnections'] = data.apply(combine_sets, variable=variable, axis=1)
    return data


def make_edges(data, variable, variable2):
    """
    Creates an edge list from resulting family layer, for one relationship. 

    Parameters:
    - data: resulting dataframe of the family layer creation
    - variable: the variable name of the PersonNr (should always be PersonNr) (or not)
    - variable2: the variablle of the relationship to be turned into an edge list

    Returns: 
    - dataframe with an edge list for that relationship 
    """
    Family_connections = data[[variable, variable2]]
    data_exploded = Family_connections.explode(variable2).reset_index(drop=True)
    data_exploded = data_exploded.dropna()
    return data_exploded

def make_entire_edge_list(family_layer): 
    """
    Creates an edge list from resulting family layer. Note the family layer has a connection indicating family households, if you dont want to include it, drop the column prior

    Parameters:
    - family_layer: resulting dataframe of the family layer creation

    Returns:
    - dataframe where the family layer is saved as an edge list
    """
    columns = family_layer.columns
    #personnr column
    first_column = columns[0]
    other_columns = columns[1:]
    result_df = pd.DataFrame()

    # Loop through other columns and apply make_edges
    for col in other_columns:
        edges_data = make_edges(family_layer, first_column, col)
        edges_data = edges_data.rename(columns={col: 'PersonNr2'})
        edges_data['connection'] = col
        result_df = pd.concat([result_df, edges_data])
    return result_df
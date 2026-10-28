
import pandas as pd
import warnings
from itertools import combinations, product
from tqdm import tqdm
import os 
import re
import sys
import pickle
import gc
import copy
import logging
import time



warnings.filterwarnings("ignore")


#Follow instructions on readme to run the code


# -------------------------------------------------------------------------------------------------
# ------------------------------------- Helper Functions ------------------------------------------
# -------------------------------------------------------------------------------------------------



def create_family_household_connection(persons):
    fam_household = {}
    for _, values_set in persons.items():
        for value in values_set:
            other_values = values_set - {value}
            fam_household[value] = other_values
    return fam_household

def sorted_alphanumeric(data):
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
    return sorted(data, key=alphanum_key)


def combine_dictionaires(dict1, dict2):
    for key, value in dict1.items():
        if key in dict2:
            dict2[key].update(value)
        else:
            dict2[key] = value

    return dict2


def Merge_dictionaries(dict1, dict2):
    res = {**dict1, **dict2}
    return res

def remove_duplicate_key_value_pairs(dict1, dict2):
    common_pairs = set()

    # Find common key-value pairs
    for key, value in dict1.items():
        if key in dict2 and dict2[key] == value:
            common_pairs.add((key, value))

    # Remove common key-value pairs from both dictionaries
    for key, value in common_pairs:
        del dict1[key]
        del dict2[key]




# -------------------------------------------------------------------------------------------------
# ------------------------------------- Wrapper function ------------------------------------------
# -------------------------------------------------------------------------------------------------

def thirty_year_family_layer(output_folder, file_list, year_beginning, personnr_variable, famid_variable):
    """
    Creates a family layer for each year (corresponding to a file list), where the information of all previous years is used

    Parameters:
    - output_folder: the name of the dictionary all the results should be saved in
    - file_list: a file containing a list with all the files
    - year_beginning: the beginning year of the data
    - personnr_variable: string indicating the name of the variable of the personnr
    - famid_variable: string specifying name of the FamId variable

    Returns:
    - saves results in the given dictionary
    """
    # Configure logging
    logging.basicConfig(filename='familylayer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    #count the years, to track variable changes and output file names
    count = copy.deepcopy(int(year_beginning))

    #code snipped to change input to a folder instead of a file_list
    
    #data_dictionary =  "FamilyLayer30years/Basic Test Data/Data_30years"
    #csv_list = os.listdir(file_list)
    #csv_list = sorted_alphanumeric(csv_list)
    #to track issues when reading in data
    skipped_previous_year = False
    different_encoding = False
    #load names from file list
    with open(file_list) as file:
        csv_list = [line.rstrip() for line in file]

    #loop through the file list /years
    for filename in tqdm(csv_list, desc="Processing  years"): 

        print("We are processing" + str(count))
        #file_name = os.path.join(file_list, filename)
        start_time = time.time()

        #should add it to the log if this does not work
        if os.path.isfile(filename):
            #need to print something out if it isnt

            #not sure if this unicode escape worked
            #data = pd.read_csv(file_path)
            #reading in data, only reading in needed columns (note in 2004 all Barn variables are present)

            #add try escape and use one of the working encodings then otherwise
            if int(count) < 2004: 
                try: 
                    data= pd.read_csv(filename, usecols=[personnr_variable, "Barn0_3", "Barn4_6", "Barn7_10", "Barn11_15", "Barn16_17", "Barn18plus", "FodelseAr", famid_variable])
                    different_encoding = False
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year:", e)
                    data= pd.read_csv(filename, usecols=[personnr_variable, "Barn0_3", "Barn4_6", "Barn7_10", "Barn11_15", "Barn16_17", "Barn18plus", "FodelseAr", famid_variable], encoding="unicode_escape")
                    logging.info(f"Year {count}: used unicode_escpae to read in data, after other failed")
                    different_encoding = True
            elif int(count) == 2004: 
                try: 
                    data= pd.read_csv(filename, usecols=[personnr_variable, "Barn0_3", "Barn4_6", "Barn7_10", "Barn11_15", "Barn16_17", "Barn18plus", "Barn18_19", "Barn20plus", "FodelseAr", famid_variable])
                    different_encoding = False
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year:", e)
                    data= pd.read_csv(filename, usecols=[personnr_variable, "Barn0_3", "Barn4_6", "Barn7_10", "Barn11_15", "Barn16_17", "Barn18plus", "Barn18_19", "Barn20plus", "FodelseAr", famid_variable], encoding= "unicode_escape")
                    logging.info(f"Year {count}: used unicode_escpae to read in data, after other failed")
                    different_encoding = True
            else:
                try: 
                    data= pd.read_csv(filename, usecols=[personnr_variable, "Barn0_3", "Barn4_6", "Barn7_10", "Barn11_15", "Barn16_17", "Barn18_19", "Barn20plus", "FodelseAr", famid_variable])
                    different_encoding = False
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year:", e)
                    data= pd.read_csv(filename, usecols=[personnr_variable, "Barn0_3", "Barn4_6", "Barn7_10", "Barn11_15", "Barn16_17", "Barn18_19", "Barn20plus", "FodelseAr", famid_variable], encoding= "unicode_escape")
                    logging.info(f"Year {count}: used unicode_escpae to read in data, after other failed")
                    different_encoding = True
            if different_encoding == True:
                try:
                    data = data.encode('utf-8')
                except Exception as e:
                    print("It was not possible to switch encoding", e)
            #create new folders for each year here 

            folder_path_final = (output_folder) + "/family_layer" + str(count)
            if not os.path.exists(folder_path_final):
                os.makedirs(folder_path_final)

            #call preprocessing function 
            data_dict, filtered_persons, current_family = preprocessing(data, count)


            #create the basic connections within the family
            parent, child, partners = create_basic_fam_connection(data_dict, filtered_persons)

            #delete variables from the memory
            del data_dict
            del filtered_persons

            #for all years except the first load the created networks from last year and combine them
            if count > int(year_beginning): 
                old_year = count-1
                folder_path_old = (output_folder) + "/family_layer" + str(old_year)

                #try loading if it does not work
                #print error
                #make it specific and add year to log file 
                issue_parent = False
                issue_child = False
                issue_partners = False
                try: 
                    with open(folder_path_old +'/parent.pkl', 'rb') as fp:
                        old_parent = pickle.load(fp)
                    #call combine function on them 
                    parent = combine_dictionaires(parent, old_parent)
                    #delete following variables to save memory
                    del old_parent
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in results from previous year:", e, "Will try reading in data from year before")
                    logging.error(f"Couldnt read in data from year before: {e}")
                    issue_parent =True
                try:  
                    with open(folder_path_old +'/child.pkl', 'rb') as fp:
                        old_child = pickle.load(fp)
                    child = combine_dictionaires(child, old_child)
                    del old_child
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in results from previous year:", e, "Will try reading in data from year before")
                    logging.error(f"Couldnt read in data from year before: {e}")
                    issue_child = True
                try: 
                    with open(folder_path_old +'/partners.pkl', 'rb') as fp:
                        old_partners = pickle.load(fp)

                    #here we call a different function, as we only want to keep one partner for each person and that is the current one
                    partners = Merge_dictionaries(old_partners, partners)
                    del old_partners
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in results from previous year:", e, "Will try reading in data from year before")
                    logging.error(f"Couldnt read in data from year before: {e}")
                    issue_partners =True

                #trying to read in a year before instead

                if issue_parent == True: 
                    old_year = count-2
                    logging.info(f"in {count}, we are trying to read in the data (parent) from 2 years ago")
                    folder_path_old = (output_folder) + "/family_layer" + str(old_year)
                    try: 
                        with open(folder_path_old +'/parent.pkl', 'rb') as fp:
                            old_parent = pickle.load(fp)
                        #call combine function on them 
                        parent = combine_dictionaires(parent, old_parent)
                        #delete following variables to save memory
                        del old_parent
                    except Exception as e:  # Catch all other exceptions
                        print("An error occurred reading in results from two previous year (parent):", e, "Will move on without previous information")
                        logging.error(f"Couldnt read in data from two previous years for the variable parent in year {count}: {e}")

                if issue_child == True: 
                    old_year = count-2
                    logging.info(f"in {count}, we are trying to read in the data (child) from 2 years ago")
                    folder_path_old = (output_folder) + "/family_layer" + str(old_year)
                    try:  
                        with open(folder_path_old +'/child.pkl', 'rb') as fp:
                            old_child = pickle.load(fp)
                        child = combine_dictionaires(child, old_child)
                        del old_child
                    except Exception as e:  # Catch all other exceptions
                        print("An error occurred reading in results from two previous year (child):", e, "Will move on without previous information")
                        logging.error(f"Couldnt read in data from two previous years for the variable child in year {count}: {e}")
                if issue_partners == True:
                    old_year = count-2
                    logging.info(f"in {count}, we are trying to read in the data (partners) from 2 years ago")
                    folder_path_old = (output_folder) + "/family_layer" + str(old_year)
                    try: 
                        with open(folder_path_old +'/partners.pkl', 'rb') as fp:
                            old_partners = pickle.load(fp)

                        #here we call a different function, as we only want to keep one partner for each person and that is the current one
                        partners = Merge_dictionaries(old_partners, partners)
                        del old_partners
                    except Exception as e:  # Catch all other exceptions
                        print("An error occurred reading in results from two previous year (partners):", e, "Will move on without previous information")
                        logging.error(f"Couldnt read in data from two previous years for the variable parents in year {count}: {e}")

            #need to check if something is wrong here
            #save the following parts of the network
            fail_count=0
            if not parent:
                fail_count += 1
                print("The layer creation resulted in empty parent connections")
            else: 
                with open(folder_path_final + '/parent.pkl', 'wb') as fp:
                    pickle.dump(parent, fp)
            if not child:
                fail_count +=1
                print("The layer creation resulted in empty child connections")
            else: 
                with open(folder_path_final + '/child.pkl', 'wb') as fp:
                    pickle.dump(child, fp)

            #check for siblings, note that we update the partners list, incase by accident we noted siblings as partners
            siblings, partners = find_siblings(parent, partners)

            #save the partner lyer of the network
            if not partners:
                fail_count +=1
                print("The layer creation resulted in empty partners connections")
            else:
                with open(folder_path_final + '/partners.pkl', 'wb') as fp:
                    pickle.dump(partners, fp)
            
            if fail_count == 3:
                skipped_previous_year == True
                print(f"Family Creation did not result in any major connections for the year {count}")
                logging.error(f"Family Creation did not result in any major connections for the year {count}")


            #find the rest of the family relationships
            grandparents, grandchildren = find_grandparents(parent, child)

            aunts_uncles, niece_nephews = find_aunts_uncles(parent, siblings)

            cousins = find_cousins(aunts_uncles, parent)

            #combine all parts of the network in one final output and save it

            print("Saving the network")
            final_output = pd.DataFrame({'parent':pd.Series(parent),'child':pd.Series(child), 'partners':pd.Series(partners), 'siblings': pd.Series(siblings), 'grandparents':pd.Series(grandparents), 'grandchildren': pd.Series(grandchildren),
                                         'aunts_uncles':pd.Series(aunts_uncles), 'niece_nephews': pd.Series(niece_nephews), 'cousins':pd.Series(cousins), 'family_household': pd.Series(current_family)})

            final_output.to_csv(folder_path_final + '/final_network' + str(count) + '.csv')

            total_nodes = final_output.shape[0]
            logging.info(f"Year {count}: Layer was saved with a total of {total_nodes} nodes.")



            #delete all this to help with memory issues
            del current_family
            del partners
            del parent
            del child
            del siblings
            del grandparents
            del grandchildren
            del aunts_uncles
            del niece_nephews
            del cousins
            del final_output
            gc.collect()
            skipped_previous_year = False
        else:
            print("No data found for year" + str(count))
            skipped_previous_year = True

        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Year {count}: Elapsed Time={elapsed_time:.2f} seconds. Creation of layer failed: {skipped_previous_year}")
        #increase count
        count+=1
    logging.shutdown() 
    return None


#function to build the family layer for one year only 
# def build_family_layer(data, count):

#     folder_path = "results/working directory_family_layer" + str(count)
#     folder_path_final = "results/family_layer" + str(count)

#     #organise this better maybe --> can use that for all layers or not?
#     folder_data = "results/data_as_json" + str(count)
#     if not os.path.exists(folder_path):
#         os.makedirs(folder_path)
#     if not os.path.exists(folder_path_final):
#         os.makedirs(folder_path_final)
#     if not os.path.exists(folder_data):
#         os.makedirs(folder_data)


#     data_dict, filtered_persons = preprocessing(data)

#     parent, child, partners = create_basic_fam_connection(data_dict, filtered_persons)


#     siblings, partners = find_siblings(parent, partners)


#     grandparents, grandchildren = find_grandparents(parent, child)

#     aunts_uncles, niece_newphews = find_aunts_uncles(parent, siblings)

#     cousins = find_cousins(aunts_uncles, parent)

#     return None



# -------------------------------------------------------------------------------------------------
# ------------------------------------- Preprocessing ---------------------------------------------
# -------------------------------------------------------------------------------------------------


def preprocessing(data, current_year):
    """
    Preprocesses the data. 

    Parameters:
    - data: a pandas dataframe containing re


    Returns:
    - data converted into a dictionary
    - data grouped by famId
    - data containting all the relationships within a famId
    """

    print("Preprocessing in progress")

    #map column names to standardize data
    if 'LopNr' in data.columns and 'LopNr_FamId' in data.columns:
        # Create a dictionary for column name mapping
        column_mapping = {'LopNr': 'PersonNr', 'LopNr_FamId': 'FamId'}
        # Use the rename method to rename columns
        data.rename(columns=column_mapping, inplace=True)

    #add column indicating if a person has a child or not
    data['Barn'] = data.filter(like='Barn').apply(lambda row: 1 if any(row > 0) else 0, axis=1)

    #add column alder_new, as alder is not present in all the data
    data['Alder_new'] = int(current_year) - data['FodelseAr']
    #check for duplicates and drop them, also print how many duplicates were dropped
    original_rows = data.shape[0]  
    data = data.drop_duplicates(subset='PersonNr', keep='first')
    dropped_duplicates = original_rows - data.shape[0] 
    total_datapoints = data.shape[0]
    logging.info(f"Amount of people in registry={total_datapoints}. {dropped_duplicates} have been dropped due to multiples of PersonNr")


    
    #transform data into a dictionary
    data_dict = data.set_index('PersonNr').to_dict(orient='index')

    print("Preprocessing: Step 1 done")
    print(f"Number of duplicates dropped: {dropped_duplicates}")

    #delete variables for memory purpose
    del dropped_duplicates
    del original_rows

    #group data by Famid
    persons2 = data.groupby('FamId')['PersonNr'].apply(lambda x: {p for p in x}).to_dict()
    filtered_persons2 = {key: value for key, value in persons2.items() if len(value) > 0}

    del persons2
    print("Preprocessing: step 2 done")
    #print(persons2)
    
    #create the connection to everyone in the Family Household for everyone
    bi_filtered = create_family_household_connection(filtered_persons2)


    print("Preprocessing Done")

    return data_dict, filtered_persons2, bi_filtered




# -------------------------------------------------------------------------------------------------
# ----------------------------- Creating the basic connections ------------------------------------
# -------------------------------------------------------------------------------------------------




def create_basic_fam_connection(data_dict, filtered_persons):
    """
    Finds  parents/child and partner relationships in data. 

    Parameters:
    - data_dict: a dictionary including registry data
    - filtered_persons: dictionary grouped by famID

    Returns:
    - dictionary with parent relationships
    - dictionary with child relationships
    - dictionary with partner relationship
    """

    partners = {}
    parent = {}
    child = {}
    #loop trough grouped data
    for key, persons in tqdm(filtered_persons.items(), desc="Fnding basic family connections"):
        
        #find all possible combinations in a Family Household
        all_combinations = []
        for r in range(2, len(persons) + 1):
            all_combinations.extend(combinations(persons, r))

        #loop through all possible combinations

        for combo in all_combinations:

            key = combo[0]
            person = combo[1]
            key_information = data_dict[combo[0]]
            couple = False
            person_information = data_dict[combo[1]]
            age_difference = abs(person_information['FodelseAr']-key_information['FodelseAr'])

            #check if the people in the combination are a couple
            if age_difference <= 13:
                couple = True
                
                #expartners are always replaced

                partners[key] = {person}
                partners[person] = {key}

            #check for partner/child relationship 
            if key_information['Barn'] == 1 and couple == False and 15<= (key_information['Alder_new'] - person_information['Alder_new'] )<=60:
                
                #checking if the age of child matches the child the parent has
                result = {key_barn: data_dict[key][key_barn] for key_barn in data_dict[key] if 'Barn' in key_barn and data_dict[key][key_barn] == 1 and key_barn != 'Barn'}
                numbers_in_keys = {number_key: [int(match) for match in re.findall(r'\d+', number_key)] for number_key in result if re.findall(r'\d+', number_key)}

                #add information to the dictionary (note we dont want to replace other existing relationship)
                for _, value_list in numbers_in_keys.items():
                    if len(value_list)>=2:
                #does not seem that efficient
                        if person_information["Alder_new"] >= value_list[0] and person_information["Alder_new"] <= value_list[1]:
                            if key in parent.keys(): 
                                parent[key].add(person)
                            else: 
                                parent[key] = {person}
                        
                            if person in child.keys():
                                child[person].add(key)
                            else: 
                                child[person] = {key}

                    else:
                        if key_information["Alder_new"] >= value_list[0]:
                
                            if key in parent.keys(): 
                                parent[key].add(person)
                            else: 
                                parent[key] = {person}
                        
                            if person in child.keys():
                                child[person].add(key)
                            else: 
                                child[person] = {key}
                        
            #checking for the relationship the other way around
            if person_information['Barn'] == 1 and couple == False and 15<= (person_information['Alder_new']-key_information['Alder_new'])<=60:
                
                # need to add the age check depending on the year
                result = {key_barn: data_dict[person][key_barn] for key_barn in data_dict[person] if 'Barn' in key_barn and data_dict[person][key_barn] == 1 and key_barn != 'Barn'}
                numbers_in_keys = {number_key: [int(match) for match in re.findall(r'\d+', number_key)] for number_key in result if re.findall(r'\d+', number_key)}
                for _, value_list in numbers_in_keys.items():
                    if len(value_list)>=2:
                        if key_information["Alder_new"] >= value_list[0] and key_information["Alder_new"] <= value_list[1]:
                            if person in parent.keys():
                                parent[person].add(key)
                            else: 
                                parent[person] = {key}
                            if key in child.keys():
                                child[key].add(person)
                            else:
                                child[key] = {person}
                            
                    else:
                        if key_information["Alder_new"] >= value_list[0]:
                            if person in parent.keys():
                                parent[person].add(key)
                            else: 
                                parent[person] = {key}
                            if key in child.keys():
                                child[key].add(person)
                            else:
                                child[key] = {person}



    return parent, child, partners



# -------------------------------------------------------------------------------------------------
# ----------------------------- Creating the other connections ------------------------------------
# -------------------------------------------------------------------------------------------------



def find_siblings(parents, partners):
    """
    Finds sibling relationships within two dictionaries of parents and partners connections. 

    Parameters:
    - parents: a dictionary including parents relationships
    - partners: a dictionary including partner relationship

    Returns:
    - dictionary with sibling relationships
    - dictionary with corrected partner relationship
    """
    siblings = {}
    #looping through all existing children of parents
    for _,  children in tqdm(parents.items(), desc="Matching siblings"):
        
        #check if a parent has more than one child
        if len(children)> 1:
            all_combinations = []
            #fin all possible combinations
            for r in range(2, len(children) + 1):

                all_combinations.extend(combinations(children, r))

            #add relationships to the dicitonary

            for combo in all_combinations:
                if combo[1] in partners.keys():
                    if partners[combo[1]]==combo[0]:
                        partners.pop(combo[1])
                if combo[0] in partners.keys():
                    if partners[combo[0]]==combo[1]:
                        partners.pop(combo[0])


                if combo[0] in siblings.keys(): 
                    
                    siblings[combo[0]].add(combo[1])
                    
                else: 
                    siblings[combo[0]] = {combo[1]}
                    
                
                if combo[1] in siblings.keys():
                    siblings[combo[1]].add(combo[0])
                else: 
                    siblings[combo[1]] = {combo[0]}

    return siblings, partners



def find_grandparents(parent, child):

    """
    Finds grandparent relationships within two dictionaries of parents and children. 

    Parameters:
    - parents: a dictionary including parents relationships
    - children: a dictionary including children relationship

    Returns:
    - dictionary with grandparent relationships
    - dictionary with grandchildren relationship
    """

    grandparents = {}
    grandchildren = {}
    

    #find common keys between parent and child
    common_keys = parent.keys() & child.keys()

    #loop through the common keys
    for key in tqdm(common_keys, desc="Finding Grandparents"): 

        grandchildren_set = parent[key]
        grandparent_set = child[key]

        #if they arent sets turn both into sets 
        if not isinstance(grandchildren_set, set):
            grandchildren_set = {grandchildren_set}
        if not isinstance(grandparent_set, set):
            grandparent_set = {grandparent_set}

        #second will always be second so thats then the grandparent and first is the grandchild

        all_combinations = list(product(grandchildren_set,grandparent_set))

        #now loop through all combinations and add them to the output
        for combo in all_combinations:

            if combo[1] in grandparents.keys(): 
                grandparents[combo[1]].add(combo[0])
            else: 
                grandparents[combo[1]] = {combo[0]}
                        
            if combo[0] in grandchildren.keys():
                grandchildren[combo[0]].add(combo[1])
            else: 
                grandchildren[combo[0]] = {combo[1]}


    return grandparents, grandchildren

def find_aunts_uncles(parent, siblings):

    
    """
    Finds aunt/uncle relationships within two dictionaries of parents and siblings. 

    Parameters:
    - parents: a dictionary including parents relationships
    - siblings: a dictionary including siblings relationship

    Returns:
    - dictionary with niece/nephew relationships
    - dictionary with aunts/uncles relationship
    """
    aunts_uncles = {}
    niece_nephew = {}
    
    #find people being a parent and a child at the same time 
    
    common_keys = parent.keys() & siblings.keys()

    for key in tqdm(common_keys, desc="Finding aunts and uncles"): 
        #if statements to check if there is one with only one element
        aunts_uncles_set = siblings[key]
        niece_nephew_set = parent[key]

        #if they arent sets turn both into sets 

        all_combinations = list(product(aunts_uncles_set,niece_nephew_set))
        for combo in all_combinations:

            if combo[1] in niece_nephew.keys(): 
                niece_nephew[combo[1]].add(combo[0])
            else: 
                niece_nephew[combo[1]] = {combo[0]}
                        
            if combo[0] in aunts_uncles.keys():
                aunts_uncles[combo[0]].add(combo[1])
            else: 
                aunts_uncles[combo[0]] = {combo[1]}
    
    return niece_nephew, aunts_uncles
    
def find_cousins(aunts_uncles, parent):

        
    """
    Finds cousines relationships within two dictionaries of aunts/uncles and parents. 

    Parameters:
    - aunts_uncles: a dictionary including aunts/uncles relationships
    - parents: a dictionary including parents relationships

    Returns:
    - dictionary with cousins relationships
    """
    cousins = {}
    common_keys = parent.keys() & aunts_uncles.keys()
    for key in tqdm(common_keys, desc="Finding cousins"): 
        cousin_set1 = parent[key]
        cousin_set2 = aunts_uncles[key]

        #create all combos
        #and add all the the dict
        all_combinations = list(product(cousin_set1,cousin_set2))
        for combo in all_combinations:

            if combo[1] in cousins.keys(): 
                cousins[combo[1]].add(combo[0])
            else: 
                cousins[combo[1]] = {combo[0]}
                        
            if combo[0] in cousins.keys():
                cousins[combo[0]].add(combo[1])
            else: 
                cousins[combo[0]] = {combo[1]}
            
    return cousins



#all the arguments needed to run the code

if len(sys.argv) < 6:
     print("Missing argument: input file name")
     sys.exit(-1)
output_folder = sys.argv[1]
file_list = sys.argv[2]
beginning_year = sys.argv[3]
personnr_variable = sys.argv[4]
famid_variable = sys.argv[5]


thirty_year_family_layer(output_folder, file_list, beginning_year, personnr_variable, famid_variable)

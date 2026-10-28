import pandas as pd
import sys
import os
import csv 
import random

from tqdm import tqdm
import logging
import time
import itertools

#function to estimate amount of outgoing edges
def power_law_function(x):
    a= 1037.18861929423
    b= 0.9857059767416111
    return a * x**(-b)

def linear_function(x):
    a= 3.1121031746058954
    b= 0.014456349204199803
    return a + b*x

#function to create education layer
def create_education_layer(personnr_variable, begin_year, file_list, output_folder):

    year = int(begin_year)

    logging.basicConfig(filename='educationlayer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    

    with open(file_list) as file:
       csv_list = [line.rstrip() for line in file]

    #loop through files to create network for each year 
    for filename in tqdm(csv_list, desc="Processing  years"):
        skipped_previous_year = False 
        start_time = time.time()
        print("Loading the data")
        if os.path.isfile(filename):
        
            if year <= 1999: 
                try: 
                    data = pd.read_csv(filename, usecols=[personnr_variable, 'Sun2000niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'Kommun'])

                    #filtering out people where we dont know exam year
                    data = data[data["ExamAr"] != "0000"]
                    
                    numeric_column = pd.to_numeric(data['ExamAr'], errors='coerce')

                    # Use boolean indexing to filter out rows where the conversion failed (resulted in NaN)
                    data = data[~numeric_column.isna()].copy()
                    data['ExamAr'] = data['ExamAr'].astype(int)
                    data = data[data['ExamAr'] >= (year-2)]
    
                    persons = data.groupby(['Sun2000niva_old', 'Sun2000niva', 'ExamAr', 'Kommun'])[personnr_variable].apply(set).to_dict()
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year, we will read in the entire dataframe:", e)
                    data = pd.read_csv(filename,  encoding="unicode_escape")
                    #convert column names so that they are the same throughout
                    if 'Sun2000niva_Old' in data.columns:
                        # Create a dictionary for column name mapping
                        column_mapping = {'Sun2000niva_Old': 'Sun2000niva_old'}

                        data.rename(columns=column_mapping, inplace=True)
                        # Use the rename method to rename columns
                    elif 'Sun2000Niva_old' in data.columns:
                        column_mapping = {'Sun2000Niva_old': 'Sun2000niva_old'}
                        data.rename(columns=column_mapping, inplace=True)

                    data = data[[personnr_variable, 'Sun2000niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'Kommun']]

                    #filtering out people where we dont know exam year
                    data = data[data["ExamAr"] != "0000"]
                    numeric_column = pd.to_numeric(data['ExamAr'], errors='coerce')

                    # Use boolean indexing to filter out rows where the conversion failed (resulted in NaN)
                    data = data[~numeric_column.isna()].copy()
                    data['ExamAr'] = data['ExamAr'].astype(int)
                    data = data[data['ExamAr'] >= (year-2)]
    
                    persons = data.groupby(['Sun2000niva_old', 'Sun2000niva', 'ExamAr', 'Kommun'])[personnr_variable].apply(set).to_dict()
                    logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")


            elif year == 2019:
                try: 
                    data = pd.read_csv(filename, usecols=[personnr_variable, 'Sun2020niva_Old', 'Sun2020niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun'])

                    data = data[data["ExamAr"] != "0000"]
                    numeric_column = pd.to_numeric(data['ExamAr'], errors='coerce')

                    # Use boolean indexing to filter out rows where the conversion failed (resulted in NaN)
                    data = data[~numeric_column.isna()].copy()
    
                    persons = data.groupby(['Sun2020niva_Old', 'Sun2020niva', 'ExamAr', 'Kommun'])[personnr_variable].apply(set).to_dict()
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year:", e)
                    data = pd.read_csv(filename, usecols=[personnr_variable, 'Sun2020niva_Old', 'Sun2020niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun'], encoding="unicode_escape")

                    data = data[data["ExamAr"] != "0000"]
                    numeric_column = pd.to_numeric(data['ExamAr'], errors='coerce')

                    # Use boolean indexing to filter out rows where the conversion failed (resulted in NaN)
                    data = data[~numeric_column.isna()].copy()
    
                    persons = data.groupby(['Sun2020niva_Old', 'Sun2020niva', 'ExamAr', 'Kommun'])[personnr_variable].apply(set).to_dict()
                    logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")
            else:
                try:
                    if year== 2018:
                        data = pd.read_csv(filename, usecols=[personnr_variable, 'Sun2000niva_Old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun', 'Kommun'])
                    else:
                        data = pd.read_csv(filename, usecols=[personnr_variable, 'Sun2000niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun', 'Kommun'])

                    #filtering out people where we do not know exam year
                    data = data[data["ExamAr"] != "0000"]
                    numeric_column = pd.to_numeric(data['ExamAr'], errors='coerce')

                    # Use boolean indexing to filter out rows where the conversion failed (resulted in NaN)
                    data = data[~numeric_column.isna()].copy()
                    #for people that dont have exam kommun -- >use kommun? 
                    persons = data.groupby(['Sun2000niva_old', 'Sun2000niva', 'ExamAr', 'ExamKommun'])[personnr_variable].apply(set).to_dict() #copy this for family layer in some parts, maybe? famid
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year:", e)
                    data = pd.read_csv(filename, usecols=[personnr_variable, 'Sun2000niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun', 'Kommun'], encoding="unicode_escape")

                    #filtering out people where we do not know exam year
                    data = data[data["ExamAr"] != "0000"]
                    numeric_column = pd.to_numeric(data['ExamAr'], errors='coerce')

                    # Use boolean indexing to filter out rows where the conversion failed (resulted in NaN)
                    data = data[~numeric_column.isna()].copy()
                    #for people that dont have exam kommun -- >use kommun? 
                    persons = data.groupby(['Sun2000niva_old', 'Sun2000niva', 'ExamAr', 'ExamKommun'])[personnr_variable].apply(set).to_dict() #copy this for family layer in some parts, maybe? famid
                    logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")

            #create dictionary
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            with open(output_folder + f'/education{year}.csv', 'w') as result_file:
                #writing each current row to save memory
                result_writer = csv.writer(result_file)
                result_writer.writerow(['PersonNr', 'PersonNr2'])
                for key, person_list in persons.items():

                    group_size= len(person_list)
                    if group_size < 1000:
                        amount_connections = round((power_law_function(group_size)*group_size*0.01))
                    else:
                        amount_connections = round(linear_function(group_size))
                    if group_size >= 1000: 
                        if year <= 1999:
                            #if year == 1992 or year== 1993:
                            #    subgroup_conditions = ['Sun2000Niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'Kommun']
                            #else:
                            subgroup_conditions = ['Sun2000niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'Kommun']
                        elif year == 2018:
                            subgroup_conditions = ['Sun2000niva_Old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun']
                        elif year == 2019:
                            subgroup_conditions = ['Sun2020niva_Old', 'Sun2020Niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun']
                        else:
                            subgroup_conditions = ['Sun2000niva_old', 'Sun2000niva', 'Sun2000Inr', 'ExamAr', 'ExamKommun']
                        
                        # Filter the data based on subgroup conditions
                        subgroup_data = data[data[subgroup_conditions].apply(tuple, axis=1).isin([key])]
                        
                        # Group the filtered data to create the subgroup
                        subgroup = subgroup_data.groupby(subgroup_conditions).apply(set)
                
                        for _, smallgroup in subgroup.items():
                            group_length = len(smallgroup)
                            #if group to small connect to bigger group
                            if group_length <= 10: 
                                
                                #connect everyone within small groups
                                pairs = itertools.combinations(smallgroup, 2)

                                for other_person in pairs:
                                    result_writer.writerow(pairs)
                                additional_connections = amount_connections- group_length

                                #add connections to larger groupings 
                                if additional_connections >0: 
                                    for person in smallgroup: 
                                        pairs = random.sample([p for p in person_list if p != person], min(additional_connections, len(person_list) - 1))
                                        for other_person in pairs:
                                            result_writer.writerow([person, other_person])
                                        #results.extend([(person, other_person) for other_person in pairs]) 
                            #skip groups larger than 10000
                            elif group_length > 10000:
                                logging.info(f"Year {year}: Grouping was too big")
                            else:
                                if group_length < 1000:
                                    amount_connections_small = round((power_law_function(group_size)*group_size*0.01))
                                else:
                                    amount_connections_small = round(linear_function(group_size))
                                if amount_connections_small > group_length:

                                    #connect everyone to everyone
                                    for edge in itertools.combinations(person_list, 2):
                                        result_writer.writerow(edge)
                                #randomely connect people within group
                                else:
                                    for person in person_list:
                                        
                                        for other_person in random.sample([p for p in person_list if p != person], min(amount_connections_small, len(person_list) - 1)):
                                            result_writer.writerow([person, other_person])
                                    
                    else: 
                        if amount_connections > group_size:

                            for edge in itertools.combinations(person_list, 2):
                                result_writer.writerow(edge)
                        else:
                            for person in person_list:
                                for other_person in random.sample([p for p in person_list if p != person], min(amount_connections, len(person_list) - 1)):
                                    result_writer.writerow([person, other_person])

        else:
            print("No data found for year" + str(year))
            logging.error(f"No data found for this {year}")
            skipped_previous_year = True
            #skipped_previous_year = True

        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Year {year}: Elapsed Time={elapsed_time:.2f} seconds. Creation of layer failed: {skipped_previous_year}")
        year += 1
    logging.shutdown()
    return None


#read in important arguments
if len(sys.argv) < 4:
     print("Missing argument: Check Readme for more information")
     sys.exit(-1)
personnr_variable = sys.argv[1]
begin_year = sys.argv[2]
file_list = sys.argv[3]
output_folder = sys.argv[4]


create_education_layer(personnr_variable, begin_year, file_list, output_folder)


import sys
import pandas as pd
import os

import itertools

import random

from tqdm import tqdm
import logging
import time
import csv
import gc


#function to estimate amount of outgoing edges
def power_law_function(x):
    a= 1037.18861929423
    b= 0.9857059767416111
    return a * x**(-b)

def linear_function(x):
    a= 3.1121031746058954
    b= 0.014456349204199803
    return a + b*x

def create_neighbourhood_layer(personnr_variable, fastbet_variable, second_variable, year, file_list, output_folder):
    # Configure logging
    logging.basicConfig(filename='neighbourhoodlayer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    year = int(year)
    skipped_previous_year = False
    with open(file_list) as file:
       csv_list = [line.rstrip() for line in file]
            

    for filename in tqdm(csv_list, desc="Processing  years"): 
        skipped_previous_year = False
        start_time = time.time()
        print("Loading the data")
        if os.path.isfile(filename):
            #different variable name in 2000 
            if year == 2000: 


                try:
                    data = pd.read_csv(filename, usecols=[personnr_variable, second_variable])
                    persons = data.groupby([second_variable])[personnr_variable].apply(set).to_dict() 
                except Exception as e:  # Catch all other exceptions
                    print("An error occurred reading in data for this year:", e)
                    data = pd.read_csv(filename, usecols=[personnr_variable, second_variable], encoding="unicode_escape")
                    persons = data.groupby([second_variable])[personnr_variable].apply(set).to_dict()
                    logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")

            else: 
                try: 
                    data = pd.read_csv(filename, usecols=[personnr_variable, fastbet_variable])
                    persons = data.groupby([fastbet_variable])[personnr_variable].apply(set).to_dict() 
                except Exception as e: 
                    print("An error occurred reading in data for this year:", e)
                    data = pd.read_csv(filename, usecols=[personnr_variable, fastbet_variable], encoding="unicode_escape")
                    persons = data.groupby([fastbet_variable])[personnr_variable].apply(set).to_dict() 
                    logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")
            del data
            gc.collect()
            #loop through the different properties
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)
            with open(output_folder + f'/neighbourhood{year}.csv', 'w') as result_file:
                result_writer = csv.writer(result_file)
                result_writer.writerow(['PersonNr', 'PersonNr2'])
                for _, person_list in tqdm(persons.items(), desc="Processing Houses"):
                    
                    group_size= len(person_list)
                    if group_size < 1000:
                        amount_connections = round((power_law_function(group_size)*group_size*0.01))
                    else:
                        amount_connections = round(linear_function(group_size))
                    if amount_connections > group_size:
                        for edge in itertools.combinations(person_list, 2):
                            result_writer.writerow(edge)
                    else: 
                        for person in person_list:
                            other_people = [p for p in person_list if p != person]
                            for other_person in random.sample(other_people, min(amount_connections, len(person_list) - 1)):
                                result_writer.writerow([person, other_person])
                            

        else: 
            print("No data found for year" + str(year))
            logging.error(f"No data found for this {year}")
            skipped_previous_year = True

        end_time = time.time()
        elapsed_time = end_time - start_time
        logging.info(f"Year {year}: Elapsed Time={elapsed_time:.2f} seconds. Creation of layer failed: {skipped_previous_year}")
        year += 1
    logging.shutdown()
    return None

if len(sys.argv) < 6:
     print("Missing argument: Check Readme for more information")
     sys.exit(-1)
personnr_variable = sys.argv[1]
fastbet_variable = sys.argv[2]
second_variable = sys.argv[3]
begin_year = sys.argv[4]
file_list = sys.argv[5]
output_folder = sys.argv[6]

create_neighbourhood_layer(personnr_variable, fastbet_variable, second_variable, begin_year, file_list, output_folder)


import pandas as pd
import os
import numpy as np
from tqdm import tqdm
import sys
import logging
import time
import random
import csv

def power_law_function(x):
	a= 1037.18861929423
	b= 0.9857059767416111
	return a * x**(-b)

def linear_function(x):
	a= 3.1121031746058954
	b= 0.014456349204199803
	return a + b*x


#combining various jobs with no explicit workplace into category remote
def convert_to_remote(value):
	try:
		int_value = int(value)
		if 99980 <= int_value <= 99999:
			if int_value in [99995, 99997]:
				return str(value)
			else:
				return "Remote"
		else:
			return str(value)
	except ValueError:
		# Value is not convertible to an integer
		return str(value)


def create_work_layer(csv_list, beginning_year, output_folder):
	year = int(beginning_year)
	logging.basicConfig(filename='worklayer.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
	with open(csv_list) as file:
	   csv_list = [line.rstrip() for line in file]
	for filename in tqdm(csv_list, desc="Processing years"): 
		skipped_previous_year = False
		start_time = time.time()
		print("Loading the data")

		# Load data: Read company id instead from PeOrgNr 
		if os.path.isfile(filename):
			if year != 2019: 
				try:
					data = pd.read_csv(filename, index_col="LopNr", usecols=["LopNr","AstKommun","AstNr_LISA","LopNr_ArbstId","LopNr_PeOrgNr"])
				except Exception as e:  # Catch all other exceptions
					print("An error occurred reading in data for this year:", e)
					data = pd.read_csv(filename, index_col="LopNr", usecols=["LopNr","AstKommun","AstNr_LISA","LopNr_ArbstId","LopNr_PeOrgNr"], encoding="unicode_escape")
					logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")
			else: 
				try: 
					data = pd.read_csv(filename, index_col="LopNr", usecols=["LopNr","AstKommun","AstNr_LISA","LopNr_ArbstId","LopNr_PeOrgNr"])
				except Exception as e: 
					print("An error occurred reading in data for this year:", e)
					data = pd.read_csv(filename, index_col="LopNr", usecols=["LopNr","AstKommun","AstNr_LISA","LopNr_ArbstId","LopNr_PeOrgNr"], encoding="unicode_escape")
					logging.info(f"Year {year}: used unicode_escpae to read in data, after other failed")
			 


			# Clean: filter ArbstId=NA
			data.dropna(subset=["LopNr_ArbstId"],inplace=True)

			# Clean: remove dups
			data=data[~data.index.duplicated(keep='first')]

			# Clean: Remove filtered kommuns
			filter_data=data[~data["AstKommun"].astype(int).isin([0,9999])]

			# Clean: Remove people with no connection to company
			filter_data=filter_data[filter_data["LopNr_PeOrgNr"]!="-"]

			print(f"After preprocessing size: {len(filter_data.index)}")

			## ---------------------------

			if not os.path.exists(output_folder):
				os.makedirs(output_folder)

			# Open writing file	
			with open(output_folder + f'/work{year}.csv', 'w') as result_file:
				result_writer = csv.writer(result_file)
				result_writer.writerow(['PersonNr', 'PersonNr2'])


				# Group by company:
				gc = filter_data[["LopNr_PeOrgNr","AstNr_LISA"]].groupby(["LopNr_PeOrgNr"],as_index=False).groups
				# Also group by company, workplace:
				gwc = filter_data[["LopNr_PeOrgNr","AstNr_LISA"]].groupby(["LopNr_PeOrgNr","AstNr_LISA"],as_index=False).groups

				print(f"Len gc: {len(gc)}, len gwc: {len(gwc)}")

				# For each company:
				for group in gc:
					# Get length
					group_size=len(gc[group])
					# LopNr values
					company_group=sorted(gc[group].values)

					# Set max edges:
					max_connections_per_workplace=200
					amount_connections=0

					# Get amount of connections based on group size
					if group_size < 1000:
						amount_connections = round((power_law_function(group_size)*group_size*0.01))
					else:
						amount_connections = round(linear_function(group_size))
					if amount_connections > group_size:
						amount_connections = group_size


					# Single person company: skip
					if group_size<=1:
						print(f"Single person company: {group}")

					# Company in size [2,200]:
					elif group_size<=max_connections_per_workplace:
						print(f"Mid company: {group}, size={group_size}, sample={min(amount_connections,group_size)}")
						# Create edges for all:
						for person in company_group:
							pairs=random.sample(company_group,min(amount_connections,group_size))
							
							for other_person in pairs:
								# Skip if person=other_person
								if person==other_person: continue
								result_writer.writerow([person,other_person])

					# Company in size >200: group by workplace
					else:
						#workplace_groups=[gr for (group,_) in gwc]
						print(f"Large company: {group}")
						# Get groups by workplace
						for group_ind in gwc:
							# Skip if not for company
							if group_ind[0]!=group: continue

							# Get workplace group
							group_w=gwc[group_ind]

							# Workplace size
							group_size_workplace=len(group_w)
							# Workplace emps
							workplace_members=sorted(group_w.values)

							# Get edge amount from workplace size
							amount_connections_workplace=0
							if group_size_workplace < 1000:
								amount_connections_workplace = round((power_law_function(group_size_workplace)*group_size_workplace*0.01))
							else:
								amount_connections_workplace = round(linear_function(group_size_workplace))
							# If connections
							if amount_connections_workplace > group_size_workplace:
								amount_connections_workplace = group_size_workplace

							print(f"Workplace: size={group_size_workplace}, sample={min(amount_connections_workplace,group_size_workplace)}")
							# Sample amount_connections from same workplace regardless of size or type.
							for person in workplace_members:
								pairs=random.sample(workplace_members,min(amount_connections_workplace,group_size_workplace))
								for other_person in pairs:
									# Skip if person=other_person
									if person==other_person: continue
									result_writer.writerow([person,other_person])   

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



if len(sys.argv) < 3:
	 print("wrong args")
	 sys.exit(-1)
csv_list = sys.argv[1]
beginning_year = sys.argv[2]
output_folder = sys.argv[3]

create_work_layer(csv_list, beginning_year, output_folder)

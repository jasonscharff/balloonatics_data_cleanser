'''
    File name: altitude_calculator.py
    Author: Jason Scharff
    Python Version: 2.7
    Description: Provides a series of functions to add altitude to all of the data even though
    the pressure data was stored in a separate file from the rest of the sensors. 
    All data matching is done using UNIX timestamps expected in each dataset.

    There is no entry point for this program. Functions are designed to be called as needed.
'''

#import the python CSV module to interface with the datasets which are all csvs.
import csv
#implement the math module to gain access to the logarithm function for the calculation of 
#altitude per the NASA model.
import math
#import the system module to get access to the MAX_INT property used in the function fill_in_missing_points
#usage explained in the documentation for that function.
import sys
#import the uuid module to append to csvs to guarantee uniqueness in filenames avoiding ovewrwrites.
import uuid

#A list of all keys to use in a master file containing all of the data
#this list will in turn be the header row on any master csv files created.
KEYS = ['time', 'calculated_altitude', 'interior_temperature', 'interior_pressure', 'interior_humidity', 'calibrated_pressure', 'geiger_cpm', 'anemometer_rpm',
        'exterior_pressure', 'exterior_humidity', 'exterior_temperature', 'sound_time',
        'blue_voltage', 'red_voltage', 'white_voltage', 'estimated_bme_altitude', 'estimated_gps_altitude',
        'gps_timestamp', 'lat', 'lat_direction', 'lng', 'lng_direction',
        'fix_quality', 'num_satelites', 'hdop', 'height_geoid_ellipsoid']


#function to concatinate all of the CSV files created during the launch into one
#single CSV. The output of this function will contain many rows with empty keys.
#arg, geiger: the filename of the csv with the data from the geiger arduino
#arg, pressure: the filename of the csv with the data from the pressure arduino.
#arg, gps: the filename of the csv with the data from the gps arduino.
#arg interior, the filename of the csv with the data from the interior pressure/temperature/humidity sensor.
def generate_combined_spreadsheet(geiger, pressure, gps, interior):
    #open the geiger counter file as a list of dictionaries.
    geiger_reader = csv.DictReader(open(geiger))
    #open the pressure file as a list of dictionaries.
    pressure_reader = csv.DictReader(open(pressure))
    #open the gps file as a list of dictionaries.
    gps_reader = csv.DictReader(open(gps))
    #open the interior pressure/humidity/temperature file as a list of dictionaries.
    interior_reader = csv.DictReader(open(interior))


    #create a new file to use as the master concatenation of all.
    with open ('master_unprocessed.csv', 'w') as new_file:
        #open this new file as a dictionary writer so rows can be written in the form of a dictionary.
        #the keys for this csv is the KEYS global variable.
        writer = csv.DictWriter(new_file, KEYS)
        #write header row (the top row listing the keys) into the newly created csv
        writer.writeheader()
        #iterate through the geiger counter file
        for row in geiger_reader:
            #add each row for the geiger counter into the master list.
            writer.writerow(row)
        for row in pressure_reader:
            #rename estimated_altitude (altitude calculation from Adafruit BME280) to estimated_bme_altitude
            #by adding a new item into the dictionary called estimated_bme_altitude equal to estimated_altitude
            row['estimated_bme_altitude'] = row['estimated_altitude']
            #remove the old name for estimated_bme_altitude from the dictionary
            row.pop('estimated_altitude')
            #write the row into the new csv.
            writer.writerow(row)
        #iterate through the gps csv.
        for row in gps_reader:
            #rename altitude (taken from gps) to estimated_gps_altitude by adding a new item
            #into the dictionary called estimated_gps_altitude equal to altitude
            row['estimated_gps_altitude'] = row['altitude']
            #remove the old name for estimated_gps_altitude from the dictionary
            row.pop('altitude')
            #write the row into the new CSV.
            writer.writerow(row)
        #iterate through the interior temperature/pressure/humidity sensor gps.
        for row in interior_reader:
            #rename temperature to interior_temperature to distinguish it from exterior_temperature
            #by adding a new key called interior_temperature equal to temperature
            row['interior_temperature'] = row['temperature']
            #remove old name for interior_temperature
            row.pop('temperature')

            #rename humidity to interior_humidity to distinguish it from exterior_humidity
            #by adding a new key called interior_humidity equal to humidity
            row['interior_humidity'] = row['humidity']
            #remove old name for interior_humidity
            row.pop('humidity')

            #rename pressure to interior_pressure to distinguish it from exterior_pressure
            #by adding a new key called interior_pressure equal to pressure
            row['interior_pressure'] = row['pressure']
            #remove old name for interior_pressure
            row.pop('pressure')

            #write row into the new CSV.
            writer.writerow(row)


generate_combined_spreadsheet('geiger.csv', 'pressure.csv', 'gps.csv', 'interior.csv')

#function to get altitude in meters from a given pressure using the NASA model
#arg pressure, the pressure to get the altitude from in pascals
def get_altitude_from_pressure(pressure):
    #convert pressure from pascals to kilopascals 
    pressure /= 1000
    #the NASA model is a piecewise function
    #if pressure is above 22.7 kilopascals apply certain function to get altitude
    if pressure > 22.707:
        #apply pressure function for pressure > 22.7 kilopascals.
        #note that for relative altitude the 101.29 should be the initial pressure
        #101.29 is just an approximation of sea level pressure from NASA.
        altitude = 44397.5-44388.3 * ((pressure/101.29) ** .19026)
    #if the pressure is less than 2.48 kilo pascals apply another function to get altitude
    elif pressure < 2.483:
        #apply pressure function for <2.483 kilopascals
        altitude = 72441.47 * ((pressure/2.488) ** -.0878) - 47454.96
    #if pressure is between 2.48 and 22.7 kilopascals apply another function to get altitude
    else:
        #apply pressure function for between 2.48 and 22.7 kilopascals.
        altitude = 11019.12 - 6369.43 * math.log(pressure/22.65)
    #return the altitude in meters
    return altitude


#function to add the altitude into the a CSV of the format generated
#by generate_combined_spreadsheet.
#arg, filename: the filename of the output from generate_combined_spreadsheet
def add_altitude_if_pressure_present(filename):
    #open the filename of the CSV in the format of the output from generate_combined_spreadsheet
    with open(filename, 'r') as original_file:
        #convert original_file as a list of dictionaries.
        reader = csv.DictReader(original_file)
        #create a new file called altitude_added
        with open('altitude_added.csv', 'w') as new_file:
            #open the new file in a manner to write dictionaries to it.
            #use the global variable KEYS (same as the output of generate_combined_spreadsheet)
            #as the keys for the new CSV
            writer = csv.DictWriter(new_file, KEYS)
            #write the header row into the CSV to define each column.
            writer.writeheader()
            #iterate through the original_file
            for row in reader:
                #if the row has real value (non-empty) value for calibrated_pressure
                if row['calibrated_pressure'] is not None and len(row['calibrated_pressure']) > 0:
                    #set the value of calculated_altitude equal to the output of the NASA model from the pressure.
                    row['calculated_altitude'] = get_altitude_from_pressure(float(row['calibrated_pressure']))
                #write the row into the new csv.
                writer.writerow(row)

add_altitude_temperature('master_unprocessed.csv')

#function to fill in missing data for a given column measurement_key in a
#csv of the format outputted by generate_combined_spreadsheet.
#arg, filename: the filename of the original file in the format of generate_combined_spreadsheet
#that contains missing values in a specific column.
#arg, measurement_key: the name of the column to fill in missing values of.
#arg, output_name the name of the file to output with no values missing in the given column.
#precondition: the CSV filename is sorted by time and all rows must have a time.
def fill_in_missing_points(filename, measurement_key, output_name):
    #open the original file
    with open(filename, 'r') as original_file:
        #convert the original file into a list of dictionaries.
        reader = csv.DictReader(original_file)
        #create a new file with the given filename
        with open (output_name, 'w') as new_file:
            #open the newly created file as a CSV to write dictionary rows into it.
            #use the global variable KEYS as the expected keys (the output of generate_combined_spreadsheet)
            writer = csv.DictWriter(new_file, KEYS)
            #write the top row (column names) on the newly created CSV.
            writer.writeheader()
            #initialize a list to store rows that need to be updated due to a missing value
            #in the column measurement_key
            rows_missing_point = []
            #initialize a variable previous_point to store the previously recorded value in the column measurement_key
            previous_point = 0
            #initialize the a variable to store the time in which previous_point was taken.
            #initialized to the max integer so that the first time on the CSV is closer to the time 
            #for the first datapoint than the initialized value so the initialization value of
            #previous_point is not used ever.
            #this actually isn't necessary based on the values of the timestamps, but is a bit better practice.
            previous_time = sys.maxint
            #iterate through the original file
            for row in reader:
                #check if there is a value in the column measurement_key for the given row
                if row[measurement_key] is not None and len(row[measurement_key]) > 0:
                    #if there is a value set variable time equal to the time that measurement was taken.
                    time = float(row['time'])
                    #iterate through a list of rows that need a value for the column measurement_key
                    for missing_row in rows_missing_point:
                        #set the variable missing_time equal to the time the measurements in the row missing
                        #a value for measurement_key were taken.
                        missing_time = float(missing_row['time'])
                        #if the time that the measurements missing a value for measurement_key
                        #were taken is closer to the time of the most for variable row
                        #than for the previous occurrence of a value in the column measurement_key.
                        if time - missing_time <= previous_time - missing_time:
                            #set the value in the row missing a value to the value in the current row
                            missing_row[measurement_key] = row[measurement_key]
                        else: #time of the last found measurement is closer to the time for missing_row
                            #set the value in the row missing a value to the previous occurrence of a value
                            #in col measurement_key 
                            missing_row[measurement_key] = previous_point

                    #set the previous measurement to the current one.
                    previous_point = row[measurement_key]
                    #set the previous time to the time of previous_point.
                    previous_time = time

                    #append the current row to the variable rows_missing_point before
                    #writing to CSV.
                    rows_missing_point.append(row)
                    #write everything from rows_missing_point into the CSV.
                    writer.writerows(rows_missing_point)
                    #reset rows_missing_point.
                    rows_missing_point = []
                else: #no measurement of interest found
                    #add the row into a list to populate with the next (or previous)
                    #occurrence of a value in the column measurement_key.
                    rows_missing_point.append(row)


#function to fill in all columns completely for a CSV in the format
#outputted by generate_combined_spreadsheet.
#arg filename, the filename to fill in the columns for.
#precondition: the CSV filename must be sorted by time and all rows must have a time.

#this functiion is structured by applying fill_in_missing_points to each column.
def fill_in_missing_data(filename):
    #remove 'time' from the list of keys in a generate_combined_spreadsheet
    #formatted file because time must be filled in for this to work
    #(a precondition of this function)
    keys = list(filter(lambda x: x != 'time', KEYS))
    #create a variable called count and set it equal to 0
    #count will be used to generate intermediate CSV files
    #with one column filled in at a time.
    count = 0
    #create a variable called previous_filename to keep track of the name of intermediate files
    #created by filling in one col at a time.
    previous_filename = filename
    for key in keys:
        #iterate through the list of keys to fill
        #call the next file count.csv to keep track of progressively made files
        #as each call to fill_in_missing_points fills only one column.
        new_filename = str(count) + '.csv'
        #completely fill the column key and name the resulting file new_filename (just the count)
        #and use the previous filename as the file to fill from so that progressive filling
        #leads to all columns being filled.
        fill_in_missing_points(previous_filename, key, new_filename)
        #set the previous_filename equal to the filename of the newly created file
        previous_filename = new_filename
        #increase the number of files created by 1. This count will then be be used for the next filename.
        count += 1


#function to do strict deduplication on CSV filename.
#removes any completely duplicate rows.
#arg filename: the name of the file to deduplicate.
def fully_deduplicate_csv(filename):
    #open the file to deduplicate and create a new file called 
    #deduped for the deduped version
    with open(filename, 'r') as in_file, open('deduped.csv', 'w') as out_file:
        #create a set to keep track of previously seen rows.
        #use a set over an array for efficient (O(1)) lookup.
        seen = set() 
        #iterate through the file to deduplicate line by line.
        for line in in_file:
            #check if we haven't seen the line before.
            if line not in seen:
                #add the line into the set seen to keep track
                seen.add(line)
                #write the line onto the new file.
                out_file.write(line)


#function to deduplicate a CSV in the format
#outputted by generate_combined_spreadsheet based on the value in column time.
#arg filename: the name of the file to deduplicate
def time_based_deduplicate_csv(filename):
    #open the file to deduplicate and created a new file called time_deduped for the deduped version.
    with open(filename, 'r') as in_file, open('time_deduped.csv', 'w') as out_file:
        #open the original file as a list of dictionaries
        reader = csv.DictReader(in_file)
        #open the newly created file as a CSV with the columns equal to the global variable KEYS
        #(the same as the output for generate_combined_spreadsheet)
        writer = csv.DictWriter(out_file, KEYS)
        #write the header row (column names) to the newly created CSV
        writer.writeheader()
        #create a set to store viewed times.
        #use a set for fast lookup
        seen = set()  
        for row in reader: #iterate through the original file
            #set the variable time = to the value of column time in the original file
            time = row['time']
            #check if this is the first time there has been an entry with the same timestamp
            if time not in seen:
                #add the time to the set seen.
                seen.add(time)
                #write the row into the deduplicated CSV.
                writer.writerow(row)

#function to create a spreadsheet with the results from simultaneously collected
#data points (sensors on the same Arduino) and altitude.
#the output of this function will be a CSV just when measurements were taken
#for the inputted keys and the altitude when those measurements were taken.
#arg, filename: the filename for the sorted output of generate_combined_spreadsheet
#arg, keys_to_include: the keys to add to the CSV along with the altitude.
#keys must be from the same Arduino so that all the data was logged together.
def filter_file(filename, keys_to_include):
    #open the base file to use as the central data soource and create a new file
    with open (filename, 'r') as original_file, open(str(uuid.uuid4()) + '.csv', 'w') as out_file:
        #create a variable called previous altitude to store the last altitude found.
        previous_altitude = -1 
        #open the original file as a list of dictionaries.
        reader = csv.DictReader(original_file)
        #create a variable called all_csv_keys to use as the columns for the output csv.
        #use time and altitude in in addition to the specified keys
        all_csv_keys = ['time', 'altitude']
        #add the specified keys into the list of keys for the outputted CSV.
        all_csv_keys.extend(keys_to_include)
        #create a csv using the newly created file with the columns in all_csv_keys
        writer = csv.DictWriter(out_file, all_csv_keys)
        #write the header row (the column names)
        writer.writeheader()
        #iterate through the original base file.
        for row in reader:
            #if an altitude is present in this row
            if row['calculated_altitude'] is not None and len(row['calculated_altitude']) > 0:
                #set previous_altitude equal to the altitude found
                previous_altitude = row['calculated_altitude']

            #create a dictionary to add to the csv with the timestamp of the current row
            #and altitude to the most recently found altitude
            dictionary = {
                'time': row['time'],
                'altitude': previous_altitude
            }
            #create a variable called error_found to set to True if this row does
            #not contain all of the keys in keys_to_include
            error_found = False
            #iterate through the keys that we want to add the altitude for.
            for key in keys_to_include:
                #set the variable val equal to the cell in the current row with the column name key
                val = row[key]
                #check if there is any measurement in the cell.
                if val is not None and len(str(val)) > 0: 
                    #add the measurement into the dictionary to write into a new CSV.
                    dictionary[key] = val
                else: #no measurement for the cell
                    error_found = True #set error_found to False to indicate that a key was missing at this row.
            if error_found == False: #if an error was not found
                writer.writerow(dictionary) #write the dictionary into the output CSV.



#function to add altitudes to use for the error bar graphs for the pressure calibration
#arg, filename: the filename of the CSV containing the pressures for the original and 2.5% and 97.5% CIs.
def confidence_interval_altitude(filename):
    #open the original file and create a new file with the altitudes
    with open (filename, 'r') as original_file, open('altitude_' + filename, 'w') as out_file:
        #the keys (column names) to use in the outputted CSV
        keys = ['interior_pressure','pressure_normal','pressure_2.5','pressure_97.5', 'altitude_50', 
        'altitude_2.5', 'altitude_97.5']
        #open the original file a list of dictionaries.
        reader = csv.DictReader(original_file)
        #create a new CSV out of the newly created file with the columns keys
        writer = csv.DictWriter(out_file, keys)
        #write the header row (the column names) of the new csv.
        writer.writeheader()
        #iterate through the input CSV.
        for row in reader:
            #calculate altitude from the 2.5% CI
            row['altitude_2.5'] = get_altitude_from_pressure(float(row['pressure_2.5']))
            #calculate altitude for the 97.5% CI
            row['altitude_97.5'] = get_altitude_from_pressure(float(row['pressure_97.5']))
            #calculate altitude for the normal calibration regression
            row['altitude_50'] = get_altitude_from_pressure(float(row['pressure_normal']))
            #write the row into the new CSV.
            writer.writerow(row)


def add_altitude_temperature(filename):
    with open(filename, 'r') as original_file, open('altitude_' + filename, 'w') as out_file:
        reader = csv.DictReader(original_file)
        writer = csv.DictWriter(out_file, ['time', 'temperature', 'altitude'])
        writer.writeheader()
        for row in reader:
            time = row['time']
            temperature = row['calibrated_temperature']
            altitude = get_altitude_from_pressure(float(row['pressure']))
            writer.writerow({'time' : time, 'temperature' : temperature, 'altitude' : altitude})

def summary_altitude(filename):
    with open(filename, 'r') as original_file, open('summary_' + filename, 'w') as out_file:
        reader = csv.DictReader(original_file)
        writer = csv.DictWriter(out_file, ['time', 'temperature', 'altitude'])
        last_alt = 0
        has_reached_descent = False
        for row in reader:
            alt = float(row['altitude'])
            if alt >= 20952:
                last_alt = alt
                has_reached_descent = True
            if has_reached_descent == True and alt - last_alt <= -1000:
                last_alt = alt
                writer.writerow(row)


s#ummary_altitude('altitude_interior_temperature.csv')
#add_altitude_temperature('interior_temperature.csv')

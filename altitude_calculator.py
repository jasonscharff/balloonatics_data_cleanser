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


    #create a new file to use as the master concatination of all.
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


#function to get altitude in meters from a given pressure using the NASA model
#arg pressure, the pressure to get the altitude from in pascals
def get_altitude_from_pressure(pressure):
    #convert pressure from pascals to kilopascals 
    pressure /= 1000
    #the NASA model is a piecwise function
    #if pressure is above 22.7 kilopascals apply certain function to get altitude
    if pressure > 22.707:
        altitude = 44397.5-44388.3 * ((pressure/101.29) ** .19026)
    #if the pressure is less than 2.48 kilopascals apply another function to get altitude
    elif pressure < 2.483:
        altitude = 72441.47 * ((pressure/2.488) ** -.0878) - 47454.96
    #if pressure is between 2.48 and 22.7 kilopascals apply another function to get altitude
    else:
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



#precondition sorted by time
def fillInMissingPoints(filename, measurement_key, output_name):
    with open(filename, 'r') as original_file:
        reader = csv.DictReader(original_file)
        with open (output_name, 'w') as new_file:
            writer = csv.DictWriter(new_file, KEYS)
            writer.writeheader()
            rows_missing_point = []
            previous_point = 0
            previous_time = sys.maxint
            for row in reader:
                if row[measurement_key] is not None and len(row[measurement_key]) > 0:
                    time = float(row['time'])
                    for missing_row in rows_missing_point:
                        missing_time = float(missing_row['time'])
                        if time - missing_time <= previous_time - missing_time:
                            missing_row[measurement_key] = row[measurement_key]
                        else:
                            missing_row[measurement_key] = previous_point

                    previous_point = row[measurement_key]
                    previous_time = time


                    rows_missing_point.append(row)
                    writer.writerows(rows_missing_point)
                    rows_missing_point = []
                else:
                    rows_missing_point.append(row)

def fillInMissingData():
    keys = list(filter(lambda x: x != 'time', KEYS))
    count = 0
    previous_filename = 'altitude_added.csv'
    for key in keys:
        new_filename = str(count) + '.csv'
        fillInMissingPoints(previous_filename, key, new_filename)
        previous_filename = new_filename
        count += 1


#fillInMissingData()


# def main():
#     generate_combined_spreadsheet(geiger='geiger.csv', pressure='pressure.csv', interior='interior.csv', gps='gps.csv')
#
# main()
#



def fullyDeduplicateCSV(filename):
    with open(filename, 'r') as in_file, open('deduped.csv', 'w') as out_file:
        seen = set()  # set for fast O(1) amortized lookup
        for line in in_file:
            if line not in seen:
                seen.add(line)
                out_file.write(line)



def mostlyDedupCSV(filename):
    with open(filename, 'r') as in_file, open('time_deduped.csv', 'w') as out_file:
        reader = csv.DictReader(in_file)
        writer = csv.DictWriter(out_file, KEYS)
        writer.writeheader()
        seen = set()  # set for fast O(1) amortized lookup
        for row in reader:
            time = row['time']
            if time not in seen:
                seen.add(time)
                writer.writerow(row)

#fullyDeduplicateCSV('imprecised_nondeduped.csv')
#mostlyDedupCSV('deduped.csv')

#generate_combined_spreadsheet('geiger.csv', 'pressure.csv', 'gps.csv', 'interior.csv')

previous_altitude = -1

def filter_file(filename, keys_to_include):
    with open (filename, 'r') as original_file, open(str(uuid.uuid4()) + '.csv', 'w') as out_file:
        global previous_altitude
        reader = csv.DictReader(original_file)
        all_csv_keys = ['time', 'altitude']
        all_csv_keys.extend(keys_to_include)
        writer = csv.DictWriter(out_file, all_csv_keys)
        writer.writeheader()
        for row in reader:
            if row['calculated_altitude'] is not None and len(row['calculated_altitude']) > 0:
                previous_altitude = row['calculated_altitude']
            print previous_altitude
            dictionary = {
                'time': row['time'],
                'altitude': previous_altitude
            }
            error_found = False
            for key in keys_to_include:
                val = row[key]
                if val is not None and len(str(val)) > 0:
                    dictionary[key] = val
                else:
                    error_found = True
            if error_found == False:
                writer.writerow(dictionary)




#addAltitudeIfPressurePresent('master_unprocessed.csv')
#filter_file('altitude_added.csv', ['blue_voltage', 'red_voltage', 'white_voltage'])


def filter_csv(filename, key, threshold):
    with open(filename, 'r') as original_file, open('thresholded_' + key + '.csv', 'w') as out_file:
        reader = csv.DictReader(original_file)
        writer = csv.DictWriter(out_file, reader.fieldnames)
        writer.writeheader()
        for row in reader:
            if row[key] is not None and len(row[key]) > 0 and float(row[key]) < threshold:
                writer.writerow(row)


#filter_csv('speed_of_sound.csv', 'sound_time', 1400)
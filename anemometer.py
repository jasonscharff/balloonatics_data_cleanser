'''
    File name: anemometer_correction.py
    Author: Jason Scharff
    Python Version: 2.7
    Description: The anemometer rpm data was collected by recording the number
    of rotations in a one minute period. However, during the launch, the variable
    to keep track of rpm was never reset to 0 after each one minute interval.
    This creates two problems:
    1. The data demonstrated a cumulative number of spins. The data should be in rpm over a minute.
    2. The cumulative values were so large they exceeded the max 16 bit integer on the Arduino
    (32,767) causing integer overflow errors where the cumulative number of spins was negative.

    Fortunately, this data is all easily recoverable by first correcting the integer overflow error
    and then finding the difference between the cumulative rotations at each minute.

    This file provides functions to fix both of the aforementioned issues to recover the data.
'''

#import csv module to interface with the input CSVs for the anemometer data
import csv

#declare a variable for the max 16 bit integer (max Arduino int)
#to correct integer overflow errors
MAX_16_BIT_INTEGER = 2 ** 15 - 1
#declare a variable for the minimum 16 bit integer (min Arduino int)
#to correct integer overflow errors
MIN_16_BIT_INTEGER = -2 ** 15


#function to correct integer overpower errors
#in anemometer data
#arg filename, the filename of the raw data to correct.
def correct_overflows(filename):
	#open the original file
    with open(filename, 'r') as original_file:
    	#convert the original file into a list of dictionaries.
        list_of_entries = csv.DictReader(original_file)
        #create a new file called overflow_corrected to use for the corrected data
        with open ('overflow_corrected.csv', 'w') as new_file:
        	#open the newly created file as a CSV with columns for time and corrected overflow anemometer_rpm
            writer = csv.DictWriter(new_file, ['time', 'anemometer_rpm'])
            #write the header (the column names)
            writer.writeheader()
            #iterate through the original file
            for dictionary in list_of_entries:
            	#set variable rpm equal to the rpm in the current row.
                rpm = int(dictionary['anemometer_rpm'])
                #if the rpm is negative then an overflow occurred.
                if rpm < 0:
                	#set the rpm equal to the max integer + the difference between the value and the min value
                	#as overflow causes a cycle.
                    rpm = MAX_16_BIT_INTEGER + (rpm - MIN_16_BIT_INTEGER)
                #create a dictionary to write to the new CSV with the overflow corrected value and the timestamp.
                new_dictionary = {'time' : dictionary['time'], 'anemometer_rpm' : rpm}
                #write the new row onto the output file.
                writer.writerow(new_dictionary)


#function to correct the fact that the anemometer rpm was never reset to 0
#by finding differences between consecutive rows.
#input file must be formatted as a CSV with columns just for time and anemometer rpm.
def correct_lack_of_reset(filename):
	#open the original file to correct.
    with open(filename, 'r') as original_file:
    	#open the original file as a list of dictionaries.
        list_of_entries = csv.DictReader(original_file)
        #create a new file called reset_corrected to use for the corrected version.
        with open ('reset_corrected.csv', 'w') as new_file:
        	#open the newly created file as a CSV with columns for time and corrected overflow anemometer_rpm
            writer = csv.DictWriter(new_file, ['time', 'anemometer_rpm'])
            #write the header (the column names)
            writer.writeheader()
            #set a variable previous rpm to 0.
            #the values are corrected by finding differences between consecutive rows, but the first row is correct
            #as the anemometer_rpm was initialized 0 at the beginning.
            previous_rpm = 0
            #iterate through the original dictionary.
            for dictionary in list_of_entries:
            	#set integer rpm equal to the rpm at the current row.
                rpm = int(dictionary['anemometer_rpm'])
                #correct this rpm by subtracting the previous row to get the difference.
                rpm -= previous_rpm
                #set variable previous_rpm to the raw (uncorrected) rpm in the row
                previous_rpm = int(dictionary['anemometer_rpm'])
                #set the value for anemometer_rpm in the row to the corrected rpm
                dictionary['anemometer_rpm'] = rpm
                #write the original row to the new CSV, but with the corrected anemometer value.
                writer.writerow(dictionary)



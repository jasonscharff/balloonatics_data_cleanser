import csv


MAX_16_BIT_INTEGER = 2 ** 15 - 1
MIN_16_BIT_INTEGER = -2 ** 15


def correct_overflows(filename):
    with open(filename, 'r') as original_file:
        list_of_entries = csv.DictReader(original_file)
        with open ('overflow_corrected.csv', 'w') as new_file:
            writer = csv.DictWriter(new_file, ['time', 'anemometer_rpm'])
            writer.writeheader()
            for dictionary in list_of_entries:
                rpm = int(dictionary['anemometer_rpm'])
                if rpm < 0:
                    rpm = MAX_16_BIT_INTEGER + (rpm - MIN_16_BIT_INTEGER)
                new_dictionary = {'time' : dictionary['time'], 'anemometer_rpm' : rpm}
                writer.writerow(new_dictionary)



def correctLackOfReset(filename):
    with open(filename, 'r') as original_file:
        list_of_entries = csv.DictReader(original_file)
        with open ('reset_corrected.csv', 'w') as new_file:
            writer = csv.DictWriter(new_file, ['time', 'anemometer_rpm'])
            writer.writeheader()
            previous_rpm = 0
            for dictionary in list_of_entries:
                rpm = int(dictionary['anemometer_rpm'])
                rpm -= previous_rpm
                previous_rpm = int(dictionary['anemometer_rpm'])
                dictionary['anemometer_rpm'] = rpm
                writer.writerow(dictionary)



#correctLackOfReset('overflow_corrected.csv')


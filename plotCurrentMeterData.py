"""
***************************************************************************
        Date of creation\change: 2021-10-27
        Version: 0.3
        contact editor(s): nilshemme@hotmail.com

***************************************************************************/
INPUT:
    - .dat/.vpd files from currentmeters, in_dir can have subfolders for stations
OUTPUT:
    .png files for each station and .csv summary for ASN reports

This script takes currentmeter files and plots them. It also generates a summary .csv table which can be used for
reporting.

User has to manually define station names and depth ranges for each station (as start and stop line numbers in raw file)
i.e.: 'S1-FG-CP01':     {'file': 'CPT_01.dat', 'start_line': 69, 'stop_line': 420},
(Please note: For Midas ECM use true line number in raw file, header will be subtracted by script)

User has to manually choose from which currentmeter model recorded the raw files
Currently supported:
- Nortek Aquadopp
- Midas ECM
"""
import os

import numpy
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import circmean, circstd

# USER INPUT
in_dir = r'F:\02_Projekte\2Africa East E14\src\plotCurrentMeterData\in\2AF East KWI02'  # dir with split raw files
out_dir = r'F:\02_Projekte\2Africa East E14\src\plotCurrentMeterData\out'  # dir to ouput joined/cleaned files
os.chdir(in_dir)  # change working dir
projectname = '2AF East KWI02'  # name of your project for output .csv i.e. 2AF East E14 B01.csv
currentmeter_model = 1  # 0 = Nortek, 1 = Midas ECM
liftup = 0.5            # limit of lift up during individual CPT pushes in meters (i.e. 0.5m should cut data reliable)

a = {'current_meter_station': {
    # USER INPUT
    # FORMAT
    # 'Station name':     {'file': 'filename.vpd', 'start_line': 69, 'stop_line': 420},
    # 'Test Marseille Port': {'file': 'FILE_010 MARSEILLE PORT.vpd', 'start_line': 55, 'stop_line': 55},
    # 'S3-SP-CP01':     {'file': 'CPT_0101.dat', 'start_line': 174, 'stop_line': 191},
    # 'S2-SP-CP01A':    {'file': 'CPT_0101.dat', 'start_line': 134, 'stop_line': 141},
    # 'S2-SP-CP01B':    {'file': 'CPT_01A01.dat', 'start_line': 27, 'stop_line': 43},
    # 'S2-SP-CP02':     {'file': 'CPT_0201.dat', 'start_line': 47, 'stop_line': 66},
    # 'KWI02-G-CP01':     {'file': 'FILE_173 VALEPORT 2AF_E14_KWI02_G_CP01.vpd', 'start_line': 55, 'stop_line': 3168},
    # 'KWI02-G-CP01':     {'file': 'FILE_173 VALEPORT 2AF_E14_KWI02_G_CP01.vpd', 'start_line': 55, 'stop_line': 3168},
    'KWI02-G-CP02':     {'file': 'FILE_171 VALEPORT 2AF_E14_KWI02_G_CP02.vpd', 'start_line': 55, 'stop_line': 2145},

}
}

# GET FILES
f = []
for (dirpath, dirnames, filenames) in os.walk(in_dir):
    for file in filenames:
        if file.endswith('.dat') and currentmeter_model == 0:
            f.append(os.path.join(dirpath, file))
        elif file.endswith('.vpd') and currentmeter_model == 1:
            f.append(os.path.join(dirpath, file))

work = []

for items in a.values():
    for key, value in items.items():
        for file in f:
            if file.endswith(value['file']):

                # Nortek Aquadopp
                if currentmeter_model == 0:
                    # Define file header
                    header = ['Month', 'Day', 'Year', 'Hour', 'Minute', 'Second', 'Errorcode', 'Statuscode',
                              'Velocity(Beam1|X|East)',
                              'Velocity(Beam2|Y|North)', 'Velocity(Beam3|Z|Up)', 'Amplitude(Beam1)', 'Amplitude(Beam2)',
                              'Amplitude(Beam3)', 'Batteryvoltage', 'Soundspeed', 'Sound Velocity', 'Heading', 'Pitch',
                              'Roll',
                              'Pressure_dbar', 'Depth', 'Temperature', 'Analoginput1', 'Analoginput2', 'Speed',
                              'Direction']
                    df = pd.read_csv(file, delim_whitespace=True, header=None, names=header)

                    # TODO this have to go
                    start_push = value['start_line'] - 1
                    stop_push = value['stop_line']

                    # DATE/TIME
                    df['Date/Time'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
                    date = df['Date/Time'].dt.date.iloc[start_push]
                    time = df['Date/Time'].dt.time.iloc[start_push]
                    df = df.set_index('Date/Time')

                    df['Diff'] = df['Depth'].diff()     # TODO testen testen testen

                # Midas ECM
                elif currentmeter_model == 1:
                    # Define file header
                    header = ['Date', 'Time', 'Depth', 'Pressure', 'Temperature', 'Velocity X', 'Velocity Y',
                              'Direction',
                              'Conductivity', 'Salinity', 'Density', 'Sound Velocity']
                    df = pd.read_csv(file, delim_whitespace=True, header=None, names=header, skiprows=54)

                    # TODO this has to go
                    start_push = value['start_line'] - 55  # Offset start/stop lines by skiprows value
                    stop_push = value['stop_line'] - 54

                    # DATE/TIME
                    date = df['Date'].iloc[start_push]
                    time = df['Time'].iloc[start_push]
                    df['Date/Time'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])
                    df = df.set_index('Date/Time')

                    # Calculate velocity vector
                    df['Speed'] = np.hypot(df['Velocity Y'].iloc[start_push:stop_push],
                                           df['Velocity X'].iloc[start_push:stop_push])

                    df['Diff'] = df['Depth'].diff()     # TODO comment

                station = key
                file_name = os.path.basename(file)

                # FIND INDIVIDUAL PUSHES
                df['OnSeabed'] = df.loc[(df['Diff'] < 0.1) & (df['Diff'] > -0.1) & (df['Depth'] > df['Depth'].max() - 0.5)]['Depth']

                df['ID'] = df['OnSeabed'].apply(lambda x: False if (np.isnan(x)) else True)
                df['Push'] = df['ID'].ne(df['ID'].shift(1)).cumsum()
                df['Push'] = np.where(np.isnan(df['OnSeabed']), 0, df['Push'])

                # SET PUSH PLOT
                push_plot = plt.figure()

                df['Depth'].plot()
                df['Diff'].plot(secondary_y=True)
                df['OnSeabed'].plot(style='o')
                df['Push'].plot(style='o')
                plt.gca.invert_yaxis()
                plt.show()


                depth = int(round(np.mean(df['Depth'].iloc[start_push:stop_push]), 0))      # Mean depth
                temp_c = round(np.mean(df['Temperature'].iloc[start_push:stop_push]), 1)    # Mean temperature
                avg_spe = round(df['Speed'].iloc[start_push:stop_push].mean(), 2)           # Avg. speed
                avg_dir = round(np.rad2deg(circmean(np.deg2rad(df['Direction'].iloc[start_push:stop_push]))), 1)    # Mean direction
                sv = round(np.mean(df['Sound Velocity'].iloc[start_push:stop_push]), 1)                             # Mean sv

                # VALUES FOR PLOT
                avg_dir_plot = circmean(np.deg2rad(df['Direction'].iloc[start_push:stop_push]))
                avg_spe_plot = df['Speed'].iloc[start_push:stop_push].mean()
                std_dir = circstd(np.deg2rad(df['Direction'].iloc[start_push:stop_push]))

                # VALUES FOR .csv
                work.append([station, file_name, date, time, depth, temp_c, avg_spe, avg_dir, sv])

                # SET POLAR PLOT
                fig = plt.figure(figsize=(8, 8))
                ax = fig.add_subplot(111, projection='polar')
                ax.set_theta_direction('clockwise')
                ax.set_theta_offset(0.5 * np.pi)

                x = np.deg2rad(df['Direction'].iloc[start_push:stop_push])
                y = df['Speed'].iloc[start_push:stop_push]

                ax.scatter(x, y, c='red')
                ax.bar(avg_dir_plot, avg_spe_plot, width=std_dir, bottom=0.0, alpha=0.5, color='red')

                degreechar = u'\N{DEGREE SIGN}'
                ax.set_xlabel('Direction [%s]' % degreechar)
                ax.set_ylabel('Current speed [m/s]')
                ax.yaxis.labelpad = 35

                plt.suptitle(station)
                ax.set_title('Mean direction: %.0f%s Mean velocity: %.2f m/s Std. dev: %.2f%s' % (
                avg_dir, degreechar, avg_spe, np.rad2deg(std_dir), degreechar))
                plot_save = os.path.join(out_dir, key + '.png')
                plt.savefig(plot_save)
                # plt.show()

                # OUTPUT
                print('-' * 69)
                print('Station:\t\t%s' % station)
                print('Date/Time:\t\t%s %s' % (date, time))
                print('Mean direction:\t%.0f%s' % (avg_dir, degreechar))
                print('Mean velocity:\t%.2f m/s' % avg_spe)
                print('Std. dev:\t\t%.2f%s' % (np.rad2deg(std_dir), degreechar))

# EXPORT .csv
results_cols = ['Station Name', 'File No.', 'Date', 'Time', 'Depth', 'Temperature', 'Speed', 'Direction',
                'Sound velocity']
results = pd.DataFrame(work, index=None, columns=results_cols)
results.to_csv(os.path.join(out_dir, projectname + '.csv'), index=False)

# OUTPUT
print('-' * 69)
print('Done!')

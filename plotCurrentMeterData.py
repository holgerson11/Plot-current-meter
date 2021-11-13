"""
***************************************************************************
        Date of creation/change: 2021-11-10
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

todo add and update instructions

User has to manually choose from which currentmeter model recorded the raw files
Currently supported:
- Nortek Aquadopp
- Midas ECM
"""

import os
from string import ascii_uppercase
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
from scipy.stats import circmean, circstd

# USER INPUT
in_dir = r'F:\02_Projekte\2Africa East E14\src\plotCurrentMeterData\in\tester'
out_dir = r'F:\02_Projekte\2Africa East E14\src\plotCurrentMeterData\out'

projectname = '2AF East KWI02'  # name of your project for output i.e. 2AF East E14 B01.csv
currentmeter_model = 1          # 0 = Nortek, 1 = Midas ECM

max_depth_delta = 0.3            # Values shallower than maximum depth of file by this value will be used
max_depth_noise = 0.15           # Cutoff value for noise in depth on seabed

debug_file = r'F:\02_Projekte\2Africa East E14\src\plotCurrentMeterData\out\2AF East KWI02_debug table.csv'

# GET FILES
f = []
os.chdir(in_dir)                # change working dir
for (dirpath, dirnames, filenames) in os.walk(in_dir):
    for file in filenames:
        if file.endswith('.dat') and currentmeter_model == 0:
            f.append(os.path.join(dirpath, file))
        elif file.endswith('.vpd') and currentmeter_model == 1:
            f.append(os.path.join(dirpath, file))

summary_table = []
debug_table = []

for file in f:
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

        # DATE/TIME setup
        df['Date/Time'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']])
        df = df.set_index('Date/Time')

    # Midas ECM
    elif currentmeter_model == 1:
        # Define file header
        header = ['Date', 'Time', 'Depth', 'Pressure', 'Temperature', 'Velocity X', 'Velocity Y',
                  'Direction',
                  'Conductivity', 'Salinity', 'Density', 'Sound Velocity']
        df = pd.read_csv(file, delim_whitespace=True, header=None, names=header, skiprows=54)

        # DATE/TIME setup
        df['Date/Time'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    # Set Date/Time as index
    df = df.set_index('Date/Time')

    # todo read debug file here for manual start stop change

    # FIND INDIVIDUAL PUSHES
    df['Diff'] = df['Depth'].diff()     # TODO explain why this works -.-
    df['OnSeabed'] = df.loc[(df['Diff'] < max_depth_noise) &
                            (df['Diff'] > -max_depth_noise) &
                            (df['Depth'] > df['Depth'].max() - max_depth_delta)]['Depth']

    df['ID'] = df['OnSeabed'].apply(lambda x: False if (np.isnan(x)) else True)
    df['Push'] = df['ID'].ne(df['ID'].shift(1)).cumsum()
    df['Push'] = np.where(np.isnan(df['OnSeabed']), 0, df['Push'])

    df_pushes = df.where(df['Push'] != 0).groupby('Push')

    push_counter = 0
    station_char = ''

    for name, group in df_pushes:
        start_push = pd.to_datetime(group['Date'].iloc[0] + ' ' + group['Time'].iloc[0])
        stop_push = pd.to_datetime(group['Date'].iloc[-1] + ' ' + group['Time'].iloc[-1])
        if len(df_pushes.groups) > 1 and push_counter > 0:
            station_char = ascii_uppercase[push_counter - 1]
        station = os.path.basename(file).split('.')[0] + station_char

        # DEBUG FILE LINE
        debug_table.append([station, start_push, stop_push])    # todo add raw file line numbers maybe??
        push_counter += 1

        file_name = os.path.basename(file)

        # Calculate velocity vector for MIDAS ECM
        if currentmeter_model == 1:
            df['Speed'] = np.hypot(df['Velocity Y'].loc[start_push:stop_push], df['Velocity X'].loc[start_push:stop_push])

        depth = int(round(np.mean(df['Depth'].loc[start_push:stop_push]), 0))      # Mean depth
        temp_c = round(np.mean(df['Temperature'].loc[start_push:stop_push]), 1)    # Mean temperature
        avg_spe = round(df['Speed'].loc[start_push:stop_push].mean(), 2)           # Avg. speed
        avg_dir = round(np.rad2deg(circmean(np.deg2rad(df['Direction'].loc[start_push:stop_push]))), 1)    # Mean direction
        sv = round(np.mean(df['Sound Velocity'].loc[start_push:stop_push]), 1)                             # Mean sv

        # VALUES FOR PLOT
        avg_dir_plot = circmean(np.deg2rad(df['Direction'].loc[start_push:stop_push]))
        avg_spe_plot = df['Speed'].loc[start_push:stop_push].mean()
        std_dir = circstd(np.deg2rad(df['Direction'].loc[start_push:stop_push]))

        # DATE/TIME for .csv
        date = df['Date'].loc[start_push]
        time = df['Time'].loc[start_push]

        # VALUES FOR .csv
        summary_table.append([station, file_name, date, time, depth, temp_c, avg_spe, avg_dir, sv])

        # SET POLAR PLOT
        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection='polar')
        ax.set_theta_direction('clockwise')
        ax.set_theta_offset(0.5 * np.pi)

        x = np.deg2rad(df['Direction'].loc[start_push:stop_push])
        y = df['Speed'].loc[start_push:stop_push]

        ax.scatter(x, y, c='red')       # todo add color scale for points for comparability
        ax.bar(avg_dir_plot, avg_spe_plot, width=std_dir, bottom=0.0, alpha=0.5, color='red')

        degreechar = u'\N{DEGREE SIGN}'
        ax.set_xlabel('Direction [%s]' % degreechar)
        ax.set_ylabel('Current speed [m/s]')
        ax.yaxis.labelpad = 35

        plt.suptitle(station)
        ax.set_title('Mean direction: %.0f%s Mean velocity: %.2f m/s Std. dev: %.2f%s' % (
            avg_dir, degreechar, avg_spe, np.rad2deg(std_dir), degreechar))
        plot_save = os.path.join(out_dir, station + '.png')
        plt.savefig(plot_save)
        # plt.show()

        # OUTPUT
        print('-' * 69)
        print('Station:\t\t%s' % station)
        print('Date/Time:\t\t%s %s' % (date, time))
        print('Mean direction:\t%.0f%s' % (avg_dir, degreechar))
        print('Mean velocity:\t%.2f m/s' % avg_spe)
        print('Std. dev:\t\t%.2f%s' % (np.rad2deg(std_dir), degreechar))


    # SET PUSH PLOT
    # todo one debug plot per station vs. push
    # todo fix plot and export
    fig = plt.figure(figsize=(12, 8))
    ax = fig.add_subplot(111)
    ax.plot(pd.to_datetime(df['Date'] + ' ' + df['Time']), df['Depth'])
    ax2 = ax.twinx()

    ax2.plot(pd.to_datetime(df['Date'] + ' ' + df['Time']), df['Diff'], color='green')  # todo maybe subplot for diff plot

    push_counter = 0
    station_char = ''

    for name, group in df_pushes:
        if len(df_pushes.groups) > 1 and push_counter > 0:      # todo station name generation as function
            station_char = ascii_uppercase[push_counter - 1]
        station = os.path.basename(file).split('.')[0] + station_char

        ax.fill_between(pd.to_datetime(group['Date'] + ' ' + group['Time']), group['Depth'], 0, color='lightblue')
        annotation_x = pd.to_datetime(group['Date'] + ' ' + group['Time']).index.max() - \
                       (pd.Timedelta(pd.to_datetime(group['Date'] + ' ' + group['Time']).index.max() -
                                     pd.to_datetime(group['Date'] + ' ' + group['Time']).index.min()) / 2)
        annotation_y = (group['Depth'].max() / 2)

        ax.annotate(station, xy=(annotation_x, annotation_y), ha='center', color='royalblue')
        push_counter += 1

    # Y AXIS
    ax.set_ylabel('Depth [m]')
    ax2.set_ylabel('%s Depth [m]' % u'\u0394')      # delta char

    # X AXIS
    dateformat = mdates.DateFormatter('%d.%m.%Y\n%H:%M:%S')
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(dateformat)
    # ax.set_xlabel('Time Day HH:MM:SS')
    # fig.autofmt_xdate()       # auto rotate label

    plot_save = os.path.join(out_dir, station + '_data.png')
    plt.savefig(plot_save)
    plt.show()


# EXPORT summary.csv
summary_cols = ['Station Name', 'File No.', 'Date', 'Time', 'Depth', 'Temperature', 'Speed', 'Direction',
                'Sound velocity']
summary = pd.DataFrame(summary_table, index=None, columns=summary_cols)
summary.to_csv(os.path.join(out_dir, projectname + '.csv'), index=False)

# EXPORT summary.csv
debug_cols = ['Station Name', 'Start push', 'Stop push']
debug = pd.DataFrame(debug_table, index=None, columns=debug_cols)
debug.to_csv(os.path.join(out_dir, projectname + '_debug table.csv'), index=False)

# OUTPUT
print('-' * 69)
print('Done!')

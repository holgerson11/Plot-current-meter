"""
***************************************************************************
        Date of creation/change:    2023-01-23
        Version:                    0.6
        Contact editor(s):          nilshemme@hotmail.com
        Documentation: https://github.com/holgerson11/Plot-current-meter
***************************************************************************/
"""

import os
from string import ascii_uppercase
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as patches
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.stats import circmean, circstd

# USER INPUT
in_dir = r'C:\test_in'
out_dir = r'C:\\out'

projectname = 'Test Project'  # name of your project for output i.e. 2AF East E14 B01.csv
currentmeter_model = 1           # 0 = Nortek Aquadopp, 1 = Midas ECM

# CUT-OFF VALUES (in [m])
# Default values: Midas ECM: 0.3 / 0.05, Nortek Auqadopp: 5 / 1
if currentmeter_model == 0:
    max_depth_delta = 5          # cut-off limit from max. depth of raw file
    max_depth_noise = 1          # cut-off limit for noise in depth
elif currentmeter_model == 1:
    max_depth_delta = 0.3
    max_depth_noise = 0.05

# CUT-OFF VALUES (in [s])
min_push_duration = 60          # min. duration on seabed to count as single push

# SCALE
max_current_speed = 0.3         # max current speed in m/s, adjust to scale colorbar


def get_station_name(filename, groupname, counter):
    station_char = ''
    stationname_org = os.path.basename(filename).split('.')[0]
    stationname = stationname_org
    if len(group) > 1 and counter > 0:
        try:
            station_char = ascii_uppercase[push_counter - 1]
        except IndexError:
            station_char = 'XX'
        stationname = stationname_org + station_char

    return stationname_org, stationname

# todo add debug mode
# todo add debug folder

# GET FILES
f = []
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
        line_offset = 0
        df = pd.read_csv(file, delim_whitespace=True, header=None, names=header)

        # DATE/TIME setup
        df['Date/Time'] = pd.to_datetime(df[['Year', 'Month', 'Day', 'Hour', 'Minute', 'Second']], format='%Y-%m-%d% %H:%M:%S.%f')

    # Midas ECM
    elif currentmeter_model == 1:
        # Define file header
        header = ['Date', 'Time', 'Depth', 'Pressure', 'Temperature', 'Velocity X', 'Velocity Y',
                  'Direction',
                  'Conductivity', 'Salinity', 'Density', 'Sound Velocity']
        line_offset = 54
        df = pd.read_csv(file, delim_whitespace=True, header=None, names=header, skiprows=line_offset)

        # DATE/TIME setup
        print(df['Date'])
        print()
        print(df['Time'])
        df['Date/Time'] = pd.to_datetime(df['Date'] + ' ' + df['Time'])

    # Set Date/Time as index
    df = df.set_index('Date/Time', drop=False)      # use Date/Time column as index and keep

    # todo read debug file here for manual start stop change

    # FIND INDIVIDUAL PUSHES
    df['Diff'] = df['Depth'].diff()     # get depth diff between lines
    df['OnSeabed'] = df.loc[(df['Diff'] < max_depth_noise) & (df['Diff'] > - max_depth_noise)]['Depth']     # depth noise cut off
    df['OnSeabed'] = np.where((df['Depth'] < df['Depth'].max() - max_depth_delta), np.nan, df['OnSeabed'])  # max depth cut off
    df['ID'] = df['OnSeabed'].apply(lambda x: False if (np.isnan(x)) else True)     # add bool for CPT on seabed
    df['Push'] = df['ID'].ne(df['ID'].shift(1)).cumsum()                            # add numbers to events
    df['Push'] = np.where(np.isnan(df['OnSeabed']), 0, df['Push'])                  # categorize events

    df_pushes = df.where(df['Push'] != 0).groupby('Push')                           # group by individual push

    push_counter = 0

    for name, group in df_pushes:                           # breaks if more then 27 pushes in one raw file
        start_push = group['Date/Time'].iloc[0]
        stop_push = group['Date/Time'].iloc[-1]
        duration_push = pd.to_timedelta(stop_push - start_push).total_seconds()
        if duration_push > min_push_duration:               # skip outlier pushes

            # GET RAW FILE LINE NUMBER
            start_push_int = df.index.get_loc(start_push) + (line_offset + 1)
            stop_push_int = df.index.get_loc(stop_push) + (line_offset + 1)

            # GET STATION NAME
            station_org, station = get_station_name(file, group, push_counter)

            # DEBUG FILE LINE
            debug_table.append([station, start_push_int, stop_push_int, start_push, stop_push])
            push_counter += 1

            file_name = os.path.basename(file)

            # Calculate velocity for MIDAS ECM
            if currentmeter_model == 1:
                df['Speed'] = np.hypot(df['Velocity Y'].loc[start_push:stop_push], df['Velocity X'].loc[start_push:stop_push])

            # VALUES FOR SUMMARY
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
            date = df['Date/Time'].dt.date.loc[start_push]
            time = df['Date/Time'].dt.time.loc[start_push]

            # VALUES FOR .csv
            summary_table.append([station, file_name, date, time, depth, temp_c, avg_spe, avg_dir, sv])

            # SET POLAR PLOT
            fig = plt.figure(figsize=(8, 8))
            ax1 = fig.add_subplot(111, projection='polar')
            ax1.set_theta_direction('clockwise')
            ax1.set_theta_offset(0.5 * np.pi)

            x = np.deg2rad(df['Direction'].loc[start_push:stop_push])
            y = df['Speed'].loc[start_push:stop_push]

            ax1.scatter(x, y, c=y, vmin=0, vmax=max_current_speed, cmap='RdYlBu')
            ax1.bar(avg_dir_plot, avg_spe_plot, width=std_dir, bottom=0.0, alpha=0.5, color='red')

            degreechar = u'\N{DEGREE SIGN}'
            ax1.set_xlabel('Direction [%s]' % degreechar)
            ax1.set_ylabel('Current speed [m/s]')
            ax1.yaxis.labelpad = 35

            plt.suptitle(station)
            ax1.set_title('Mean direction: %.0f%s Mean velocity: %.2f m/s Std. dev: %.2f%s' % (
                avg_dir, degreechar, avg_spe, np.rad2deg(std_dir), degreechar))
            plt.tight_layout()
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
            print('Duration: \t\t%.1f s' % duration_push)

    # DEBUG PLOT
    # Depth plot
    fig = plt.figure(figsize=(12, 8))
    gs = gridspec.GridSpec(3, 3, figure=fig)
    ax2 = fig.add_subplot(gs[-1, :3])
    ax1 = fig.add_subplot(gs[:2, :3], sharex=ax2)       # 2 row x 1 col grid, position 1
    ax1.plot(df['Date/Time'], df['Depth'])

    # Diff plot
    ax2.plot(df['Date/Time'], df['Diff'], color='green')

    # ADD CUT OFF RECTANGLES
    start = mdates.date2num(df['Date/Time'].index.max())
    end = mdates.date2num(df['Date/Time'].index.min())
    width = end - start
    # x, y, width, height
    rect = patches.Rectangle((start, df['Depth'].max()), width, max_depth_delta * -1, linewidth=1, edgecolor='r', fill=False)
    rect2 = patches.Rectangle((start, max_depth_noise), width, max_depth_noise * -2, linewidth=1, edgecolor='r', fill=False)
    ax1.add_patch(rect)
    ax2.add_patch(rect2)

    push_counter = 0
    colors = plt.cm.tab10(np.linspace(0, 1, len(df_pushes)))

    for name, group in df_pushes:
        stationname_org, station = get_station_name(file, group, push_counter)

        ax1.fill_between(group['Date/Time'], group['Depth'], 0, color=colors[push_counter])
        annotation_x = group['Date/Time'].index.max() - \
                       (pd.Timedelta(group['Date/Time'].index.max() - group['Date/Time'].index.min()) / 2)
        annotation_y = (group['Depth'].max() / 2)

        ax1.annotate(station, xy=(annotation_x, annotation_y), ha='center', color='white')
        push_counter += 1

    # Y AXIS
    ax1.yaxis.grid(True, which='Major', linestyle='--', alpha=0.5)
    ax2.yaxis.grid(True, which='Major', linestyle='--', alpha=0.5)
    ax1.set_ylabel('Depth [m]')
    ax2.set_ylabel('%s Depth [m]' % u'\u0394')      # delta char
    ax1.invert_yaxis()

    # X AXIS
    ax1.xaxis.grid(True, which='Major', linestyle='--', alpha=0.5)
    ax2.xaxis.grid(True, which='Major', linestyle='--', alpha=0.5)
    dateformat = mdates.DateFormatter('%d.%m.%Y\n%H:%M:%S')
    plt.setp(ax1.get_xticklabels(), visible=False)
    ax2.xaxis.set_major_formatter(dateformat)

    plt.suptitle('%s' % file)
    plot_save = os.path.join(out_dir, stationname_org + '_debug.png')
    plt.tight_layout()
    plt.savefig(plot_save)
    # plt.show()

# EXPORT summary.csv
summary_cols = ['Station Name', 'File No.', 'Date', 'Time', 'Depth', 'Temperature', 'Speed', 'Direction',
                'Sound velocity']
summary = pd.DataFrame(summary_table, index=None, columns=summary_cols)
summary.to_csv(os.path.join(out_dir, projectname + '.csv'), index=False)

# EXPORT debug.csv
debug_cols = ['Station Name', 'Start Line Number', 'Stop Line Number', 'Start push', 'Stop push']
debug = pd.DataFrame(debug_table, index=None, columns=debug_cols)
debug.to_csv(os.path.join(out_dir, projectname + '_debug table.csv'), index=False)

# OUTPUT
print('-' * 69)
print('Done!')

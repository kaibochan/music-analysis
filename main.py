# This program uses the songs.json file produced by compile.py to produce
# a histogram showing how much music I have made over time

from math import ceil
from sys import argv
from json import load
from datetime import datetime, timedelta
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from process import MusicThroughput
from compile import Song

# Graph the music histogram
def graph_histogram(music_histogram: list[MusicThroughput], bin_size_days, years_to_show):
    history_to_show = years_to_show * timedelta(days=365).total_seconds()

    # Filter histogram to only show backwards a specified amount of years
    music_histogram_filtered = \
        list(filter(lambda x: datetime.now().timestamp()
                    - x.start_time.timestamp() < history_to_show,
                    music_histogram))
    
    # Set up skip modulus variable to skip however many labels to ensure
    # the graph has a max of 30 labels, making it more readable
    labels_to_show_max = 30
    skip_mod = ceil(len(music_histogram_filtered) / labels_to_show_max)

    # t is a list of the start_times for each bin
    t = []
    # m is the throughput of music for each bin
    m = []
    # lbls is a list of the x-axis labels
    lbls = []

    total_time = 0
    max_tp = None
    for i, bin_data in enumerate(music_histogram_filtered):
        t.append(bin_data.start_time.timestamp())

        # Find total music time and max throughput across all bins
        m.append(bin_data.throughput)
        total_time += bin_data.throughput
        if max_tp is None or bin_data.throughput > max_tp.throughput:
            max_tp = bin_data

        # Leave every other label blank for spacing
        if i % skip_mod == 0:
            # labels are in the format MM/YY
            lbls.append(f'{bin_data.start_time.month}/'
                        + f'{bin_data.start_time.day}/'
                        + f'{bin_data.start_time.year - 2000}')
        else:
            lbls.append('')
    
    # Display overall statistics about histogram
    max_start = f'{max_tp.start_time.month}/{max_tp.start_time.day}/'\
        + f'{max_tp.start_time.year - 2000}'
    max_end = f'{max_tp.end_time.month}/{max_tp.end_time.day}/'\
        + f'{max_tp.end_time.year - 2000}'
    print(f'Total music made between: {total_time:.1f} seconds')
    print(f'Maximum music made between {max_start} - {max_end}: '
          + f'{max_tp.throughput:.1f} seconds')

    # Graph histogram
    df = pd.DataFrame({'time': t, 'throughput': m})

    sns.set_style('whitegrid')
    ax = sns.barplot(data=df, x='time', y='throughput', orient='v', width=1.0)

    ax.set(xlabel=f'Time (tΔ = {bin_size_days:.1f} days)',
           ylabel='Total music made (seconds)',
           title=f'Total Music Made Per Every {bin_size_days:.1f} Days')

    plt.xticks(range(len(t)), labels=lbls, rotation=-60)
    plt.show()

# Compiles all songs into a histogram, depicting when (over some time delta)
# and how much music in total over said time delta
def main():
    expected_parameters = '(float)bin_size_days, [(float)years_to_show]'
    try:
        bin_size_days = float(argv[1])
    except ValueError:
        print('Mismatch parameter type.\nExpected: ' + expected_parameters)
        return
    except IndexError:
        print(f'Received {len(argv) - 1} parameters.\n'
              + 'Expected: ' + expected_parameters)
        return

    try:
        years_to_show = float(argv[2])
    except ValueError:
        print('Mismatch parameter type.\nExpected: ' + expected_parameters)
        return
    except IndexError:
        years_to_show = datetime.now().year

    songs = []

    # Load from songs.json into songs list
    with open('songs.json') as f:
        data = load(f)
        for obj in data:
            songs.append(Song(obj['name'], obj['length'],
                              obj['creation_time']))

    music_histogram = MusicThroughput.create_histogram(songs, bin_size_days)

    graph_histogram(music_histogram, bin_size_days, years_to_show)


if __name__ == "__main__":
    main()
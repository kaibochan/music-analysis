# This program uses the songs.json file produced by compile.py to produce
# a histogram showing how much music I have made over time

from sys import argv
from time import strftime, gmtime
from json import load
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from process import MusicThroughput
from compile import Song

# print the bin date, total length, and list of songs
def print_bin_data(bin_data: MusicThroughput):
    print(f'{bin_data.start_time.date()}\t'
              + strftime('%H:%M:%S', gmtime(bin_data.throughput)))

    songs_list = ''
    for song in bin_data.songs:
        songs_list += f'{song}, '
    songs_list = songs_list.removesuffix(', ')
    print(f'\t{songs_list}')

# Graph the music histogram
def graph_histogram(music_histogram: list[MusicThroughput]):
    total_time = 0

    # t is a list of the start_times for each bin
    t = []
    # m is the throughput of music for each bin
    m = []
    # lbls is a list of the x-axis labels
    lbls = []
    for i, bin_data in enumerate(music_histogram):      
        t.append(bin_data.start_time.timestamp())
        m.append(bin_data.throughput)
        total_time += bin_data.throughput

        # Leave every other label blank for spacing
        if i % 2 == 0:
            # labels are in the format MM/YY
            lbls.append(f'{bin_data.start_time.month}/'
                        + f'{bin_data.start_time.year - 2000}')
        else:
            lbls.append('')
    
    print(f'Total music made: {total_time}')

    df = pd.DataFrame({'time': t, 'throughput': m})
    sns.barplot(data=df, x='time', y='throughput', orient='v')
    plt.xticks(range(len(t)), labels=lbls, rotation=-60)
    plt.show()

# Compiles all songs into a histogram, depicting when (over some time delta)
# and how much music in total over said time delta
def main():
    try:
        bin_size_days = float(argv[1])
    except ValueError:
        print('Mismatch parameter type, expected a float')
        return
    except IndexError:
        print(f'Received {len(argv) - 1} parameters, expected 1')
        return

    songs = []

    # Load from songs.json into songs list
    with open('songs.json') as f:
        data = load(f)
        for obj in data:
            songs.append(Song(obj['name'], obj['length'],
                              obj['creation_time']))

    music_histogram = MusicThroughput.create_histogram(songs, bin_size_days)

    graph_histogram(music_histogram)


if __name__ == "__main__":
    main()
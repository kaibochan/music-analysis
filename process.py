from __future__ import annotations
from datetime import datetime, timedelta
from math import ceil
from compile import Song

# Contains time interval as well as total music made during
class MusicThroughput:
    def __init__(self, start_time: datetime, end_time: datetime,
                 songs_made: list[Song]) -> None:
        self.start_time: datetime = start_time
        self.end_time: datetime = end_time
        self.songs: list[Song] = songs_made
        
        self.throughput: float = 0
        for song in self.songs:
            self.throughput += song.length

    # Returns true if some was made within the range [start_time, end_time)
    @classmethod
    def was_song_made_between(cls, start_time: datetime,
                            end_time: datetime, song: Song) -> bool:
        song_date = datetime.fromtimestamp(song.creation_time)
        return song_date >= start_time and song_date < end_time

    # Returns an ordered list of MusicThroughput objects
    @classmethod
    def create_histogram(cls, songs: list[Song], bin_size_in_days: float
                  ) -> tuple[list[MusicThroughput], float]:
        songs.sort()

        bin_size = timedelta(bin_size_in_days).total_seconds()
        earliest_time_unix = songs[0].creation_time
        latest_time_unix = songs[-1].creation_time
        num_bins = ceil((latest_time_unix - earliest_time_unix) / bin_size)

        histogram = [None] * num_bins
        for i, bin in enumerate(histogram):
            start_time = datetime.fromtimestamp(earliest_time_unix + i * bin_size)
            end_time = datetime.fromtimestamp(earliest_time_unix +(i + 1)
                                            * bin_size)
            
            songs_made = list(filter(lambda song: 
                cls.was_song_made_between(start_time, end_time, song), songs))

            histogram[i] = cls(start_time, end_time, songs_made)
        
        return histogram
    
# This program pulls from preset locations and an exported bookmarks file
# in order to save the song information into a json file for later analysis
# Preset locations: "{KAISTUFF}:\Creating\Music\analog",
#                   "{KAISTUFF}:\Creating\Music\beepbox"
# Bookmarks file must be named "bookmarks.html"

from functools import total_ordering
from json import dumps
from os import listdir
from os.path import getmtime, getsize, samefile, basename, splitext
from bs4 import BeautifulSoup as bs
from selenium.webdriver import Firefox, ActionChains
from selenium.webdriver import FirefoxOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.wait import WebDriverWait
from tqdm import tqdm
from mutagen.wave import WAVE
from mutagen.mp3 import MP3
from wmi import WMI

supported_audio_extensions = (".wav", ".mp3")

# Holds data about the song file such as the path, name, and length
@total_ordering
class SongFile:
    def __init__(self, song_full_path: str):
        self.file_path: str = song_full_path
        self.file_name: str = basename(self.file_path)

        path_splitext = splitext(self.file_path)
        self.name: str = basename(path_splitext[0])
        self.audio_format: str = path_splitext[1]

        if not (self.audio_format in supported_audio_extensions):
            raise ValueError(f"Unsupported audio format: {self.audio_format}")
        
        self._init_song_metadata()
        self._init_file_metadata()
    
    # Initialize metadata relating to the music
    def _init_song_metadata(self) -> None:
        if self.audio_format == ".wav":
            self._mutagen_handle: WAVE = WAVE(self.file_path)
        elif self.audio_format == ".mp3":
            self._mutagen_handle: MP3 = MP3(self.file_path)
        
        self.length: float = self._mutagen_handle.info.length
    
    # Initialize metadata relating to file stats
    def _init_file_metadata(self) -> None:
        self.creation_time = getmtime(self.file_path)
        self.size = getsize(self.file_path)

    def __str__(self) -> str:
        return self.name
    
    def _is_valid_operand(self, other: object) -> bool:
        return (hasattr(other, "name")
                and hasattr(other, "creation_time"))
    
    # Two song files are only equivalent if they are the same file (same path)
    def __eq__(self, other: object) -> bool:
        if not self._is_valid_operand(other):
            return NotImplemented
        return samefile(self.file_path, other.file_path)

    # Comparisons are done based on creation time of the song
    def __lt__(self, other: object) -> bool:
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.creation_time < other.creation_time


# Holds the basic information all songs have, whether they are from a file
# or from another location
@total_ordering
class Song:
    def __init__(self, name: str, length: float, creation_time: float):
        self.name = name
        self.length = length
        self.creation_time = creation_time
    
    def __str__(self) -> str:
        return f"{self.creation_time}\t{self.length:<4.1f} {self.name}"
    
    def _is_valid_operand(self, other: object) -> bool:
        return (hasattr(other, "name")
                and hasattr(other, "creation_time"))
    
    # Two songs are equivalent if they have the same name
    def __eq__(self, other: object) -> bool:
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.name == other.name
    
    # Comparisons are done based on creation time of the song
    def __lt__(self, other: object) -> bool:
        if not self._is_valid_operand(other):
            return NotImplemented
        return self.creation_time < other.creation_time


# Main purpose is to compile a list of songs in the form of their file paths
class SongCompiler:

    # Returns true if the file is a wave or mp3 file
    # file must be an absolute path
    @classmethod
    def is_audio_file(cls, file: str) -> bool:
        return file.endswith(supported_audio_extensions)

    # Compiles a list of audio file paths from predefined directories
    @classmethod
    def get_songs_from_files(cls) -> list[Song]:

        beepbox_path = f"C:\\Users\\kaibu\\Documents\\Kai-Stuff\\Creating\\Music\\beepbox"
        analog_path = f"C:\\Users\\kaibu\\Documents\\Kai-Stuff\\Creating\\Music\\analog"

        beepbox_filenames = listdir(beepbox_path)
        analog_filenames = listdir(analog_path)

        all_filepaths = []

        for file in beepbox_filenames:
            all_filepaths.append(beepbox_path + "\\" + file)

        for file in analog_filenames:
            all_filepaths.append(analog_path + "\\" + file)
        
        song_file_paths = filter(lambda file:
                                 SongCompiler.is_audio_file(file),
                                 all_filepaths)
        
        songs = []
        for song_filepath in song_file_paths:
            song_file = SongFile(song_filepath)
            songs.append(Song(song_file.name, song_file.length,
                              song_file.creation_time))
            
        return songs

    # Retrieves the all links, add_times, and names from music_bookmarks.html
    @classmethod
    def get_bookmarked_songs_info(cls) -> tuple[list[str], list[str],
                                                list[float]]:
        
        bookmarks = "bookmarks.html"
        names = []
        links = []
        times = []

        soup = bs(open(bookmarks).read(), features="lxml")
        songs_header = soup(lambda tag:
                            tag.name == "h3" and tag.text == "Songs")[0]
        songs_list = songs_header.find_parent().next_sibling.find_all("a")

        # Retrieve song information and link for each item in Songs
        for link in songs_list:
            names.append(link.text)
            links.append("https://jummbus.bitbucket.io/#"
                         + link["href"].split("#")[1])
            times.append(float(link["add_date"]))

        return (names, links, times)

    @classmethod
    def get_songs_from_bkmk(cls) -> list[Song]:
        info = cls.get_bookmarked_songs_info()
        songs = []
        
        # Initialize web driver
        webdriver_service = Service("C:/Program Files/GeckoDriver/geckodriver.exe")
        options = FirefoxOptions()
        driver = Firefox(service=webdriver_service, options=options)

        for i, _ in tqdm(enumerate(info[0])):

            # Open song link
            driver.get(info[1][i])

            try:
                # Click file menu
                xpath = "//div[@class='selectContainer menu file']/select[1]"
                file_dropdown = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, xpath)))
                ActionChains(driver).move_to_element(file_dropdown).click()\
                    .perform()

                # Select export option
                select = Select(file_dropdown)
                select.select_by_value("export")

                # Get song length
                xpath = "//div[@class='prompt noSelection']"
                export_menu = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.XPATH, xpath)))
                xpath = ".//div[2]//div[1]"
                length_element = export_menu.find_element(By.XPATH, xpath)
                mins, secs = length_element.text.split(":")
                length = float(mins) * 60 + float(secs)
                
                song = Song(info[0][i], length, info[2][i])
                songs.append(song)

            except:
                print(f"Failed to retrieve song length of {info[0][i]}")
        
        driver.quit()
        
        return songs
    
    # Compiles a list of all songs
    @classmethod
    def get_all_songs(cls) -> list[Song]:
        file_songs = cls.get_songs_from_files()
        bkmk_songs = cls.get_songs_from_bkmk()

        # Compile all songs into list
        songs = file_songs + bkmk_songs

        # Sort by name for ease of duplicate checking
        sorted(songs, key=lambda song:song.name)

        # Remove the duplicate song(s) with later creation time
        i = 1
        while i < len(songs):
            if songs[i] == songs[i - 1]:
                if songs[i].creation_time < songs[i - 1].creation_time:
                    del songs[i - 1]
                else:
                    del songs[i]
            else:
                i += 1

        songs.sort()

        # If any two songs have the same creation time, it is very likely bad
        # data and is removed from the list; which to remove is arbitrary
        i = 1
        while i < len(songs):
            if songs[i].creation_time == songs[i - 1].creation_time:
                del songs[i - 1]
            else:
                i += 1

        return songs
    
    @classmethod
    def save_songs_json(cls):
        songs = cls.get_all_songs()

        json_string = dumps(songs, default=lambda o: o.__dict__, indent=4,
                            sort_keys=True)
        with open("songs.json", "w") as f:
            f.write(json_string)


if __name__ == "__main__":
    SongCompiler.save_songs_json()
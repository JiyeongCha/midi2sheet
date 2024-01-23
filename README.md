# midi2sheet
Convert midi files to score using music21

## Dependencies
* OS : LINUX

* Programming language: Python 3.6+

* Python Library
  * Music21 (for convert midi to sheet)
  * pretty-midi (for handling midi data)
  * Numpy
  * Argparse
  * Pathlib


## Using STP from the command line
~~~python
python midi2sheet.py -i ../midi2sheet/midi/test.mid  -o ../sheet

[optional arguments]
  -i path_audio           Path to input midi file (default: '../midi2sheet/midi/test.wav')
  -o path_save_sheet      Path to folder for saving sheet file (default: '../sheet')
  -a path_save_array      Path to folder for saving array file (default: '../array')
  -t tempo                Tempo of song (default: 66)
  -s time_sig             Time signature of song (default: '4/4')
~~~

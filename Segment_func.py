import re
from music21 import *
import pretty_midi
import numpy as np
from key_dict import key_dict
from utils import *

def filter_out_vib(segment, tempo):
    """ Filter out and Delete vibrato from .mid file
        allowable_rate : Half(0.5) of the sixteenth note is determined by vibrato
    ----------
    Parameters:
        segment : List of segments in a midi file (list) (onset, offset, pitch)
        tempo : tempo (int)

    """
    segment_del_vib = []
    allowable_rate = (60 / (4 * tempo)) * 0.5
    for i in range(len(segment)):
        gap = segment[i][1] - segment[i][0]

        if gap < allowable_rate:
            if i == 0:
                segment[i + 1] = [segment[i][0], segment[i + 1][1], segment[i + 1][2]]
                segment_del_vib.append(segment[i + 1])
                i += 1

            elif 0 < i < len(segment) - 1:
                gap_plus = segment[i + 1][1] - segment[i + 1][0]
                gap_minus = segment[i - 1][1] - segment[i - 1][0]
                if gap_plus < allowable_rate:
                    segment[i - 1] = [segment[i - 1][0], segment[i][1], segment[i - 1][2]]
                    segment_del_vib.append(segment[i - 1])
                else:
                    if gap_minus < allowable_rate:
                        segment[i + 1] = [segment[i][0], segment[i + 1][1], segment[i + 1][2]]
                        segment_del_vib.append(segment[i + 1])
                    else:
                        if gap_minus < gap_plus:
                            segment[i + 1] = [segment[i][0], segment[i + 1][1], segment[i + 1][2]]
                            segment_del_vib.append(segment[i + 1])

                        elif gap_minus > gap_plus:
                            segment[i - 1] = [segment[i - 1][0], segment[i][1], segment[i - 1][2]]
                            segment_del_vib.append(segment[i - 1])

            elif i == len(segment) - 1:
                segment[i - 1] = [segment[i - 1][0], segment[i][1], segment[i - 1][2]]
                segment_del_vib.append(segment[i - 1])
        else:
            segment_del_vib.append(segment[i])

    return segment_del_vib


def del_overlap(segment):
    """ Delete overlap element from Segment list deleted vibrato
    ----------
    Parameters:
        segment : List of segments without vibrato (list) ; Output of Filter_out_vib()

    """
    for i in range(len(segment) - 1):
        if i < len(segment) - 1:
            if segment[i][0] == segment[i + 1][0]:
                del segment[i]

            elif segment[i][1] == segment[i + 1][1]:
                del segment[i + 1]

            elif segment[i][0] == segment[i + 1][0] and segment[i][1] == segment[i + 1][1]:
                del segment[i]

        elif i == len(segment) - 1:
            if segment[i - 1][0] == segment[i][0]:
                del segment[i]

            elif segment[i - 1][1] == segment[i][1]:
                del segment[i]

            elif segment[i][0] == segment[i - 1][0] and segment[i][1] == segment[i - 1][1]:
                del segment[i]

    return segment


def del_same_element(segment):
    """ Delete same element(onset, offset) from Segment list
    ----------
    Parameters:
        segment : List of segments without vibrato and overlap element (list) ; Output of Del_overlap()

    """
    complete_segment = []

    for i in range(len(segment)):
        if segment[i][0] != segment[i][1]:
            complete_segment.append(segment[i])

    return complete_segment


def separate_rest(segment):
    """ Separate Rest segment from edited segment list
    ----------
    Parameters:
        segment : Complete segment list of segments with vibrato modifications (list) ; Complete_Segment (Output of Del_SameElement)

    """
    rest_list = []
    for i in range(len(segment) - 1):
        duration = segment[i + 1][0] - segment[i][1]
        rest_list.append(duration)

    rest_list.insert(0, segment[0][0])

    return rest_list


def separate_note(segment):
    """ Separate Note segment from edited segement list
    ----------
    Parameters:
        segment : Complete segment list of segments with vibrato modifications (list) ; Complete_Segment (Output of Del_SameElement)

    """
    for i in range(len(segment) - 1):
        interval = segment[i + 1][0] - segment[i][1]
        segment[i + 1] = [segment[i + 1][0] - interval,
                          segment[i + 1][1] - interval,
                          segment[i + 1][2]]

    return segment


def rest_quantize(rest_segment, quarter_sec):
    """ Quantize Rest segment list on the basis of sixteenth note
    ----------
    Parameters:
        rest_segment : Rest segment list separated from segment list [start, end] (list) ; Output of Separate_Rest
        quarter_sec : Seconds of sixteenth note (int)

    """
    for i in range(len(rest_segment)):
        if rest_segment[i] % quarter_sec != 0:
            if (rest_segment[i] / quarter_sec) - (rest_segment[i] // quarter_sec) < 0.5:
                rest_segment[i] = quarter_sec * (rest_segment[i] // quarter_sec)
                continue

            elif rest_segment[i] < quarter_sec * 0.5:
                rest_segment[i] = 0.0
                continue

            elif quarter_sec * 0.5 < rest_segment[i] <= quarter_sec:
                rest_segment[i] = quarter_sec
                continue

            else:
                rest_segment[i] = quarter_sec * (rest_segment[i] // quarter_sec) + quarter_sec
                continue

    return rest_segment


def note_quantize(note_segment, quarter_sec):
    """ Quantize Note segment list on the basis of sixteenth note
    ----------
    Parameters:
        note_segment : Note segment list separated from segment list [start, end, pitch] (list) ; Output of Separate_Note()
        quarter_sec : Seconds of sixteenth note (int)

    """
    for i in range(len(note_segment)):
        gap = note_segment[i][1] - note_segment[i][0]
        if i == 0:
            note_segment[i] = [0.00, (quarter_sec * (round(gap / quarter_sec))), note_segment[i][2]]

        else:
            note_segment[i] = [note_segment[i - 1][1],
                               note_segment[i - 1][1] + (quarter_sec * (round(gap / quarter_sec))),
                               note_segment[i][2]]
    return note_segment


def odd_num_quantize(note_segment, quarter_sec):
    """ Quantize Note segment list on the basis of odd-numbered sixteenth note
        except : sixteenth note, dotted eighth note
    ----------
    Parameters:
        note_segment : Note segment list separated from segment list [start, end, pitch] (list)
        quarter_sec : Seconds of sixteenth note (int)

    """
    for i in range(len(note_segment)):
        gap = note_segment[i][1] - note_segment[i][0]
        gap_minus = note_segment[i - 1][1] - note_segment[i - 1][0]

        num_16th = round(gap / quarter_sec)

        if num_16th != 1 and num_16th != 3 and num_16th % 2 != 0:
            note_segment[i][1] = note_segment[i][0] + (quarter_sec * (num_16th - 1))
            for edit in range(i + 1, len(note_segment)):
                e_gap = note_segment[edit][1] - note_segment[edit][0]
                note_segment[edit] = [note_segment[edit - 1][1],
                                      note_segment[edit - 1][1] + (quarter_sec * (round(e_gap / quarter_sec))),
                                      note_segment[edit][2]]
                continue

    return note_segment


def combine_segment(note_segment, rest_segment):
    """ Combine Rest and Note segments
        Not essential step ; If you want to get a quantized Segment list, do this step
    ----------
    Parameters:
        note_segment : Quantized Note segment list [start, end, pitch] (list) ; Output of Odd_Num_Quantize()
        rest_segment : Quantized Rest segment list [start, end] (list) ; Output of Rest_Quantize()

    """
    for i in range(len(note_segment) - 1):
        if i < len(note_segment) - 1:
            note_segment[i] = [note_segment[i][0] + rest_segment[i],
                               note_segment[i][1] + rest_segment[i],
                               note_segment[i][2]]
            for edit in range(i + 1, len(note_segment) - 1):
                note_segment[edit] = [note_segment[edit][0] + rest_segment[i],
                                      note_segment[edit][1] + rest_segment[i],
                                      note_segment[edit][2]]

        note_segment[-1] = [note_segment[-1][0] + sum(rest_segment),
                            note_segment[-1][1] + sum(rest_segment),
                            note_segment[-1][2]]

    return note_segment


def note_element_list(segment, quarter_sec):
    """ Pre-processing step for note element before sheet.append()
    ----------
    Parameters:
        segment : Quantized Note segment list [start, end, pitch] (list) ; Output of Odd_Num_Quantize()
        quarter_sec : Seconds of sixteenth note (int)

    """
    note_name_list = []
    note_list = []
    duration_list = []
    for i in range(len(segment)):
        note_pitch = str(pitch.Pitch(segment[i][2]))
        note_list.append(note_pitch)

        gap = segment[i][1] - segment[i][0]
        duration_list.append(round(gap / quarter_sec) * 0.25)

    for i in range(len(note_list)):
        note_name = f"n{str(i)}"
        note_name_list.append(note_name)

    note_element = list(zip(note_name_list, note_list, duration_list))

    return note_element


def rest_element_list(rest_segment, quarter_sec):
    """ Pre-processing step for rest element before sheet.append()
    ----------
    Parameters:
        rest_segment : Quantized Rest segment list (list)
        quarter_sec : Seconds of sixteenth note (int)

    """
    rest_name_list = []
    rest_str_list = []
    rest_duration_list = []
    for i in range(len(rest_segment)):
        rest_str_list.append('Rest')

        rest_duration_list.append(round(rest_segment[i] / quarter_sec) * 0.25)

        rest_name = f"r{str(i)}"
        rest_name_list.append(rest_name)

    rest_element = list(zip(rest_name_list, rest_str_list, rest_duration_list))

    return rest_element


def combine_note_and_rest(note_element, rest_element):
    """ Combine Rest and Note elements
    ----------
    Parameters:
        note_element : Pre-processed note element [Rest_Name, 'Rest', rest_duration] (list)
        rest_element : Pre-processed rest element [Note_Name, pitch, note_duration] (list)

    """
    combine_list = []
    for i in range(len(note_element)):
        if i < len(note_element) - 1:
            combine_list.append(rest_element[i])
            combine_list.append(note_element[i])
        else:
            combine_list.append(note_element[i])

    return combine_list


def note_and_rest_info(element_list):
    """ Append note information to an empty stream
    ----------
    Parameters:
        element_list : Combined list with note and rest elements (list) ; Output of Combine_NoteAndRest()

    """
    sheet = stream.Stream()
    for info in element_list[:]:
        note_name = info[0]
        note_pitch = info[1]
        note_duration = info[2]

        if note_duration == 0.0:
            pass
        else:
            if note_pitch != 'Rest':
                note_name = note.Note(note_pitch)
                note_name.duration.quarterLength = note_duration
                sheet.append(note_name)
            else:
                note_name = note.Rest()
                note_name.duration.quarterLength = note_duration
                sheet.append(note_name)

    return sheet


def get_key_signature(midi_path):
    """ Estimate Key signature from .mid file
    ----------
    Parameters:
        midi_path : Path of midi file (str)

    """
    midi_file = converter.parse(midi_path)
    key = midi_file.analyze('key')
    midi_key = key_dict[str(key)]

    return midi_key


def save_sheet(sheet, key_signature, Tempo, file_name, time_signature, fmt_type, save_path):
    """ Append note information to an empty stream
    ----------
    Parameters:
        sheet : Combined list with note and rest elements (list)
        key_signature : key signature (int)
        Tempo : tempo (int)
        file_name : title name (str)
        time_signature : time_signature (str)
        fmt_type : fmt type you want
        ('musicxml', 'text', 'midi', 'lily', 'lilypond', 'lily.png', 'lily.pdf', 'lily.svg', 'musicxml.png' ...)
        save_path : Path of .png save file (str)

    """
    sheet.insert(0, metadata.Metadata())  # title 넣으려면 해야함
    sheet.metadata.title = file_name
    sheet.timeSignature = meter.TimeSignature(time_signature)
    sheet.keySignature = key.KeySignature(key_signature)
    sheet.insert([0, tempo.MetronomeMark(number=Tempo)])
    check_and_make_dir(save_path)
    sheet.show(fmt=f'{fmt_type}', fp=save_path)
    # sheet.show()

##########

def midi_to_segment(filename):
    """ Convert .mid to segment
    ----------
    Parameters:
        filename: .mid (str)

    ----------
    Returns:
        segments: [start(s),end(s),pitch] (list)
    """

    pm = pretty_midi.PrettyMIDI(filename)
    segment = []
    for note in pm.instruments[0].notes:
        segment.append([note.start, note.end, note.pitch])
    return segment


def segment_to_midi(segments, path_output, tempo=120):
    """ Convert segment to .mid
    ----------
    Parameters:
        segments: [start(s),end(s),pitch] (list)
        path_output: path of save file (str)
    """
    pm = pretty_midi.PrettyMIDI(initial_tempo=int(tempo))
    inst_program = pretty_midi.instrument_name_to_program("Acoustic Grand Piano")
    inst = pretty_midi.Instrument(program=inst_program)
    for segment in segments:
        note = pretty_midi.Note(
            velocity=100, start=segment[0], end=segment[1], pitch=np.int(segment[2])
        )
        inst.notes.append(note)
    pm.instruments.append(inst)
    pm.write(f"{path_output}")

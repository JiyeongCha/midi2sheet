import re
from music21 import *
import pretty_midi
import numpy as np
from key_dict import key_dict
from Segment_func import *
import argparse
import pathlib


def estimate_downbeat(args):
    PATH_PROJECT = pathlib.Path(__file__).absolute().parent.parent

    """ Save array file """
    segment = midi_to_segment(args.midi_path)
    np.save(args.path_save_array, segment)

    """ Load array file to list """
    seg_array_file = np.load(args.path_save_array)
    segment_list = seg_array_file.tolist()
    raw_segment_list = seg_array_file.tolist()

    """ Estimate Downbeat """
    # convert first note time to 0
    first_note = segment_list[0][0]
    for num in range(len(segment_list)):
        segment_list[num] = [segment_list[num][0] - first_note,
                             segment_list[num][1] - first_note,
                             segment_list[num][2]]

    segment_to_midi(segment_list, path_output=f"{PATH_PROJECT}/output/{file_name}_0.00.mid",
                    tempo=args.tempo)

    midi_path_DB = f"{PATH_PROJECT}/output/{file_name}_0.00.mid"
    midi_data = pretty_midi.PrettyMIDI(midi_path_DB)
    downbeat_list = (midi_data.get_downbeats()).tolist()
    downbeat = downbeat_list[1]

    return raw_segment_list, downbeat


def main(args):
    segment_list, downbeat = estimate_downbeat(args)
    # Tempo = round(240 / int(downbeat))
    Tempo = args.tempo
    quarter_sec = downbeat / 16
    print(f'Downbeat = {downbeat}, Tempo = {Tempo}')

    """ Delete Vibrato """
    del_vib_seg = filter_out_vib(segment_list, Tempo)
    del_vib_seg = del_overlap(del_vib_seg)
    del_vib_seg = del_same_element(del_vib_seg)

    """ Saparate Each segment list """
    rest_list = separate_rest(del_vib_seg)
    note_list = separate_note(del_vib_seg)

    """ Quantize Each segment list """
    quantized_rest = rest_quantize(rest_list, quarter_sec)
    quantized_note = note_quantize(note_list, quarter_sec)
    quantized_note = odd_num_quantize(quantized_note, quarter_sec)

    """ (Not essential) Save Quantized midi file """
    temp = combine_segment(quantized_note, quantized_rest)
    segment_to_midi(temp, path_output=f"{PATH_PROJECT}/output/{file_name}_edit.mid", tempo=Tempo)

    """ Make Sheet Element """
    note_element = note_element_list(quantized_note, quarter_sec)
    rest_element = rest_element_list(quantized_rest, quarter_sec)

    combine_element = combine_note_and_rest(note_element, rest_element)

    """ Make Sheet And Save Image """
    sheet = note_and_rest_info(combine_element)

    key = get_key_signature(args.midi_path)
    save_sheet(sheet, key_signature=key, Tempo=Tempo, file_name=file_name, time_signature=args.time_sig,
               fmt_type = 'musicxml', save_path=args.path_save_sheet)



if __name__ == "__main__":
    PATH_PROJECT = pathlib.Path(__file__).absolute().parent.parent
    file_name = "breath"
    parser = argparse.ArgumentParser(description="Convert MIDI to Sheet")
    parser.add_argument(
        "-i",
        "--midi_path",
        type=str,
        help="Path to input midi file.",
        default=f"{PATH_PROJECT}/output/{file_name}.mid",
    )

    parser.add_argument(
        "-o",
        "--path_save_sheet",
        type=str,
        help="Path to folder for saving sheet file",
        default=f"{PATH_PROJECT}/sheet/{file_name}",
    )

    parser.add_argument(
        "-a",
        "--path_save_array",
        type=str,
        help="Path to folder for saving array file",
        default=f"{PATH_PROJECT}/array/{file_name}.npy",
    )

    parser.add_argument(
        "-t",
        "--tempo",
        type=int,
        help="Tempo of song",
        default=62,
    )

    parser.add_argument(
        "-s",
        "--time_sig",
        type=str,
        help="Time signature of song",
        default='4/4',
    )

    args = parser.parse_args()
    estimate_downbeat(parser.parse_args())
    main(parser.parse_args())

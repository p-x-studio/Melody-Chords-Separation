"""
Converts all the midi in a folder to C major or A minor

Original by: https://gist.github.com/aldous-rey/68c6c43450517aa47474
"""

import glob
import os
import music21
import pretty_midi
from tqdm import tqdm

# conversions dict
majors = dict([
    ("G#", 4),("A", 3),("A#", 2),("B", 1),("C", 0),("C#", -1),("D", -2),("D#", -3),("E", -4),("F", -5),("F#", 6),("G", 5),
    ("A-", 4),("A", 3),("B-", 2),("B", 1),("C", 0),("D-", -1),("D", -2),("E-", -3),("E", -4),("F", -5),("G-", 6),("G", 5)  
])
minors = dict([
    ("G#", 1),("A", 0),("A#", -1),("B", -2),("C", -3),("C#", -4),("D", -5),("D#", 6),("E", 5),("F", 4),("F#", 3),("G", 2),
    ("A-", 1),("A", 0),("B-", -1),("B", -2),("C", -3),("D-", -4),("D", -5),("E-", 6),("E", 5),("F", 4),("G-", 3),("G", 2)
])

def transpose_file(midi_file_in, midi_file_out, half_steps):
    out = {}

    # read input
    midi_data = pretty_midi.PrettyMIDI(midi_file_in)

    for c, instrument in enumerate(midi_data.instruments):
        out[c] = []
        for note in instrument.notes:
            note_pitch = note.pitch + half_steps
            note_start = note.start
            note_end = note.end

            temp_note = [note_start, note_end, note_pitch]
            out[c].append(temp_note)
    
    # write out
    out_midi = pretty_midi.PrettyMIDI()
    piano_program = pretty_midi.instrument_name_to_program('Acoustic grand piano')
    
    for c in out.keys():
        piano = pretty_midi.Instrument(program=piano_program)
        current_midi_track = out[c]
        
        for note in current_midi_track:
            pretty_midi_note = pretty_midi.Note(velocity=127, pitch=note[2], start=note[0], end=note[1])
            piano.notes.append(pretty_midi_note)

        out_midi.instruments.append(piano)
    
    out_midi.write(midi_file_out)

def convert_folder(in_folder, out_folder):
    files_list = glob.glob(os.path.join(in_folder, '*.mid'))

    for file in tqdm(files_list[:15], desc='Transposing to C major / A minor'):
        score = music21.converter.parse(file)

        try:
            key = score.analyze('key')
            if key.mode == "major":
                half_steps = majors[key.tonic.name]
            elif key.mode == "minor":
                half_steps = minors[key.tonic.name]

            out_file_path = os.path.join(out_folder, os.path.basename(file))
            transpose_file(file, out_file_path, half_steps) # an alternative would be to use music21.transpose but unfortunately it is bugged

            new_score = music21.converter.parse(out_file_path)
            key = new_score.analyze('key')
            assert (key.tonic.name == 'C' or key.tonic.name == 'A') and (key.mode == 'major' or key.mode == 'minor'), f'Conversion failed: {key.tonic.name} {key.mode}'
        except Exception as e:
            print(e)

if __name__ == '__main__':
    output_folder = '../dataset/wikifonia/output/'
    output_transposed_folder = '../dataset/wikifonia/output_transposed/'

    convert_folder(output_folder, output_transposed_folder)
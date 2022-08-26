import glob
import os
import zipfile
import json
import transposer
from tqdm import tqdm
from score_to_midi import score_to_midi

input_raw_folder = '../dataset/wikifonia/input/'
input_xml_folder = '../dataset/wikifonia/input_xml/'

input_folder = input_xml_folder
output_folder = '../dataset/wikifonia/output/'

output_transposed_folder = '../dataset/wikifonia/output_transposed/'

convert_to_xml = False
convert_to_transposed = True

def mxl_to_xml(in_file_path, out_folder_path, out_file_name):
    with zipfile.ZipFile(in_file_path, 'r') as zip_ref:
        zip_ref.extract('musicXML.xml', out_folder_path)
    
    os.replace(os.path.join(out_folder_path, 'musicXML.xml'), os.path.join(out_folder_path, out_file_name))

def convert_folder_to_xml(input_raw_folder):
    mxl_files = glob.glob(os.path.join(input_raw_folder, '*.mxl'))

    for f in tqdm(mxl_files, desc='Converting .mxl to .xml'):
        file_name = os.path.basename(f)
        file_name_xml = file_name.replace('.mxl', '.xml')

        mxl_to_xml(f, input_xml_folder, file_name_xml)

def convert_xml_to_mid(input_folder, output_folder):
    out_of_chords = {}
    c_right = 0
    c_wrong = 0
    
    xml_files = glob.glob(os.path.join(input_folder, '*.xml'))

    for f in tqdm(xml_files, desc='Converting .xml to .mid'):
        file_name = os.path.basename(f)
        file_name_mid = file_name.replace('.xml', '.mid')
        file_path_out = os.path.join(output_folder, file_name_mid)
            
        try:
            score_to_midi(f, file_path_out, verbose=False)
            c_right += 1
        except Exception as e:
            if 'Chord' in str(e):
                chord_name = str(e).split(':')[1].strip()
                if chord_name not in out_of_chords:
                    out_of_chords[chord_name] = file_name
            
            c_wrong += 1
    
    c_total = c_right + c_wrong
    percentage_right = round(c_right / c_total * 100, 2)
    percentage_wrong = round(c_wrong / c_total * 100, 2)

    print(f'\nTotal: {c_total}\nRight: {c_right} ({percentage_right}%)\nWrong: {c_wrong} ({percentage_wrong}%)')
    print('\nWrong chords:')
    print(json.dumps(out_of_chords, indent=4, sort_keys=True))
    print('')

def main():
    if convert_to_xml:
        convert_folder_to_xml(input_raw_folder)

    convert_xml_to_mid(input_folder, output_folder)

    if convert_to_transposed:
        transposer.convert_folder(output_folder, output_transposed_folder)

main()
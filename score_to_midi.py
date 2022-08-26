"""
This script converts a MusicXML file into a midi one with melody and chords separated in two distinct tracks.

Originally based on: https://github.com/qsdfo/musicxml_parser
"""

import numpy as np
import xml.sax
import re
import os
import tempfile
import logging
import pretty_midi
from total_length_handler import TotalLengthHandler

# mapping table for note to midi conversion
mapping_step_midi = {
	'C': 0,
	'D': 2,
	'E': 4,
	'F': 5,
	'G': 7,
	'A': 9,
	'B': 11
}

# mapping table for chord name to midi conversion
# scraped from https://en.wikipedia.org/wiki/List_of_chords
# TODO: 6, 7, 9
mapping_harmony_steps = {
	"augmented": [0, 4, 8],
	"augmented-eleventh": [0, 4, 7, 10, 2, 6], 
	"augmented-major-seventh": [0, 4, 8, 11], 
	"augmented-seventh": [0, 4, 8, 10], 
	"augmented-ninth": [0, 4, 8, 10, 2], # TODO: check
	# "augmented-sixth": [0, 4, 100, 4, 6, 100, 4, 7, 10], 
	"diminished": [0, 3, 6], 
	"dim": [0, 3, 6], 
	"diminished-major-seventh": [0, 3, 6, 11], 
	"diminished-seventh": [0, 3, 6, 9], 
	"dominant": [0, 4, 7], 
	"dominant-11th": [0, 4, 7, 10, 2, 5], 
	"dominant-minor-ninth": [0, 4, 7, 10, 1], 
	# "dominant-ninth": [0, 4, 7, 10, 2],  # TODO: check
	"dominant-ninth": [0, 7, 10, 2 + 12], 
	"dominant-parallel": [0, 3, 7], 
	"dominant-seventh": [0, 4, 7, 10], 
	"dominant-seventh-flat-five": [0, 4, 6, 10], 
	# "dominant-seventh-sharp-nine-/-hendrix": [0, 4, 7, 10, 3], 
	"dominant-13th": [0, 4, 7, 10, 2, 5, 9], 
	"dream": [0, 5, 6, 7], 
	"elektra": [0, 7, 9, 1, 4], 
	"farben": [0, 8, 11, 4, 9], 
	"half-diminished": [0, 3, 6, 10], 
	"m7b5": [0, 3, 6, 10], 
	"harmonic-seventh": [0, 4, 7, 10], 
	"leading-tone-triad": [0, 3, 6], 
	"lydian": [0, 4, 7, 11, 6], 
	"magic": [0, 1, 5, 6, 10, 0, 3, 5], 
	"major": [0, 4, 7], 
	"major-eleventh": [0, 4, 7, 11, 2, 5], 
	"major-seventh": [0, 4, 7, 11], 
	"maj7": [0, 4, 7, 11], 
	"major-seventh-sharp-eleventh": [0, 4, 8, 11, 6], 
	"major-sixth": [0, 4, 7, 9], 
	"major-sixth-ninth": [0, 4, 7, 9, 2],
	"maj69": [0, 4, 7, 9, 2], 
	"major-ninth": [0, 4, 7, 11, 2], 
	"major-13th": [0, 4, 7, 11, 2, 6, 9], 
	"major-minor": [0, 3, 7, 11], 
	"mediant": [0, 3, 7], 
	"minor": [0, 3, 7], 
	"min": [0, 3, 7], 
	"minor-11th": [0, 3, 7, 10, 2, 5], 
	"minor-major": [0, 3, 7, 11], 
	"minMaj7": [0, 3, 7, 11], 
	"minor-ninth": [0, 3, 7, 10, 2],
	"min9": [0, 3, 7, 10, 2],  
	"minor-seventh": [0, 3, 7, 10], 
	"min7": [0, 3, 7, 10], 
	"minor-sixth": [0, 3, 7, 9],
	"min6": [0, 3, 7, 9], 
	"minor-sixth-ninth-(6/9)": [0, 3, 7, 9, 2], 
	"minor-thirteenth": [0, 3, 7, 10, 2, 5, 9], 
	"minor-13th": [0, 3, 7, 10, 2, 5, 9], 
	"mystic": [0, 6, 10, 4, 9, 2], 
	"neapolitan": [1, 5, 8], 
	"ninth-augmented-fifth": [0, 4, 8, 10, 2], 
	"ninth-flat-fifth": [0, 4, 6, 10, 2], 
	"northern-lights": [1, 2, 8, 0, 3, 6, 7, 10, 11, 4, 7], 
	# "\"ode-to-napoleon\"-hexachord": [0, 1, 4, 5, 8, 9], 
	"petrushka": [0, 1, 4, 6, 7, 10], 
	"power": [0, 7], 
	"psalms": [0, 3, 7], 
	"secondary-dominant": [0, 4, 7], 
	"secondary-leading-tone": [0, 3, 6], 
	"secondary-supertonic": [0, 3, 7], 
	"seven-six": [0, 4, 7, 9, 10], 
	"seventh-suspension-four": [0, 5, 7, 10], 
	"sus47": [0, 5, 7, 10], 
	"so-what": [0, 5, 10, 3, 7], 
	"suspended-fourth": [0, 5, 7], 
	"suspended-second": [0, 2, 7], 
	"subdominant": [0, 4, 7], 
	"subdominant-parallel": [0, 3, 7], 
	"submediant": [0, 3, 7], 
	"subtonic": [0, 4, 7], 
	"supertonic": [0, 3, 7], 
	# "thirteenth-flat-ninth": [0, 4, 7, 10, 1, null, null], 
	# "thirteenth-flat-ninth-flat-fifth": [0, 4, 6, 10, 1, null, null], 
	"tonic-counter-parallel": [0, 3, 7], 
	"tonic": [0, 4, 7], 
	"tonic-parallel": [0, 3, 7], 
	"tristan": [0, 3, 6, 10], 
	# "viennese-trichord": [0, 1, null, 6, 7]
}

class scoreToMidiHandler(xml.sax.ContentHandler):
	"""
	Defines the xml.sax handler that converts parsed MusicXML file
	to midi
	"""
	def __init__(self, total_length, out_path, remove_silence = True):
		"""
		Initalizes the handler class

		Parameters
		----------
		total_length : int
			the total length in number of quarter note of the parsed file
			(this information can be accessed by first parsing the file with the TotalLengthHandler)
		out_path : str
			path to the output midi file
		remove_silence : boolean (default: True)
			if true, remove silence at the beginning of the midi file
		"""
		self.current_element = u""
		self.content = u""
		self.remove_silence = remove_silence

		# Measure informations
		self.time = 0 # time counter
		self.division_score = -1 # rhythmic quantization of the original score (in division of the quarter note)
		self.beat = -1
		self.beat_type = -1
		self.bar_length = -1

		# Current note information
		# Pitch
		self.pitch_set = False
		self.step = u""
		self.step_set = False
		self.octave = 0
		self.octave_set = False
		self.alter = 0
		# Is it a rest ?
		self.rest = False
		# Is it a chord ? (usefull for the staccati)
		self.chord = False
		# Harmony information
		self.harmony = False
		self.root_step = u''
		self.root_step_set = False
		self.kind = u''
		self.kind_set = False
		self.harmony_alter = 0

		self.harmony_start_time = -1
		self.harmony_prev_root_step = u''
		self.harmony_prev_kind = u''
		self.harmony_prev_alter = 0
		# Time
		self.duration = 0
		self.duration_set = False
		# Voices are used for the articulation
		self.current_voice = u''
		self.voice_set = False

		# Midi out
		self.note_list = []
		self.harmony_note_list = []
		self.bpm = 120
		self.total_length = total_length
		self.out_path = out_path

		# Tied notes (not phrasing)
		self.tie_type = None
		self.tying = {}  # Contains voice -> tie_on?
		# Staccati . Note that for chords the staccato tag is
		# ALWAYS on the first note of the chord if the file is correctly written
		self.previous_staccato = False
		self.staccato = False

	def compute_chords(self, time_midi):
		"""
		This method computes the end of a chord

		Parameters
		----------
		time_midi : float
			The current time marker converted to midi
		"""
		harmony_end_time = time_midi

		# check if chord duration is valid
		if harmony_end_time > self.harmony_start_time:
			# compute base pitch
			base_pitch = mapping_step_midi[self.harmony_prev_root_step] + self.octave * 12 + self.harmony_prev_alter
			
			# add pitch with steps based on chord kind
			if self.harmony_prev_kind in mapping_harmony_steps:
				for i in mapping_harmony_steps[self.harmony_prev_kind]:
					current_chord_pitch = base_pitch + i
					self.harmony_note_list.append([self.harmony_start_time, harmony_end_time, current_chord_pitch])
				
				logging.debug(f"[HARMONY] Finishing: {self.harmony_prev_root_step} ({self.harmony_prev_alter}) {self.harmony_prev_kind} - start time: {self.harmony_start_time} - end time: {harmony_end_time} ({self.time}) - base pitch: {base_pitch} - alter: {self.harmony_prev_alter}")
			else:
				raise NameError(f'Chord type not present in dictionary: {self.harmony_prev_kind}')
		else:
			logging.debug(f'[HARMONY] Duration not valid - start time: {self.harmony_start_time} - end time: {harmony_end_time}')

	def startElement(self, tag, attributes):
		"""
		This callback is called when the beginning of a tag is found

		Parameters
		----------
		tag : str
			The name of the tag
		attributes : dictionary
			A dictionary with every key being an attribute having their corresponding values
		"""
		self.current_element = tag

		# Part information
		if tag == u"part":
			# Set to zeros time information
			self.time = 0
			self.division_score = -1
			# Initialize the midi
			# TODO: Check if this instrument has already been seen ?
			self.note_list = []

		if tag == u'harmony':
			self.harmony = True

		if tag == u'note':
			self.not_played_note = False
			if u'print-object' in attributes.keys():
				if attributes[u'print-object'] == "no":
					self.not_played_note = True

		if tag == u'rest':
			self.rest = True

		if tag == u'chord':
			if self.duration_set:
				raise NameError('A chord tag should be placed before the duration tag of the current note')
			self.time -= self.duration
			self.chord = True

		if tag == u'tie':
			self.tie_type = attributes[u'type']

		if tag == u'staccato':
			self.staccato = True

	def endElement(self, tag):
		"""
		This callback is called when the end of a tag is found

		Parameters
		----------
		tag : str
			The name of the tag
		"""

		# convert time in score to time in midi (seconds)
		time_midi = ( 60.0 / self.bpm ) * self.time / self.division_score

		if tag == u'pitch':
			if self.octave_set and self.step_set:
				self.pitch_set = True
			self.octave_set = False
			self.step_set = False

		# chords handling
		if tag == u'harmony':
			if self.root_step_set and self.kind_set:
				if self.harmony_start_time != -1: # if not the beginning of the first chord
					self.compute_chords(time_midi) # compute end of the chord

				self.harmony_prev_root_step = self.root_step
				self.harmony_prev_alter = self.harmony_alter
				self.harmony_prev_kind = self.kind
				self.harmony_start_time = time_midi

				logging.debug(f"[HARMONY] Starting: {self.root_step} ({self.harmony_alter}) {self.kind} - start time: {time_midi} ({self.time})")
				
		# notes handling
		if tag == u"note":
			if not self.duration_set:
				logging.debug("[WARNING] XML misformed, a Duration tag is missing")
				raise NameError('XML misformed, a Duration tag is missing')

			not_a_rest = not self.rest
			note_played = not self.not_played_note
			if not_a_rest and note_played:
				# Check file integrity
				if not self.pitch_set:
					logging.debug("[WARNING] XML misformed, a Pitch tag is missing")
					raise NameError('XML misformed, a Pitch tag is missing')
				 
				# start, end, duration, pitch
				start_time_midi = time_midi
				duration_midi = ( 60.0 / self.bpm ) * self.duration / self.division_score
				end_time_midi = (time_midi + duration_midi) 
				midi_pitch = mapping_step_midi[self.step] + self.octave * 12 + self.alter

				temp_note = [start_time_midi, end_time_midi, midi_pitch]
				self.note_list.append(temp_note)
				logging.debug(f"[NOTE] start: {start_time_midi} - end: {end_time_midi} - pitch: {midi_pitch}")

				voice = u'1'
				if self.voice_set:
					voice = self.current_voice

				# Initialize if the voice has not been seen before
				if voice not in self.tying:
					self.tying[voice] = False

				# Note that tying[voice] can't be set when opening the tie tag since
				# the current voice is not knew at this time
				if self.tie_type == u"start":
					# Allows to keep on the tying if it spans over several notes
					self.tying[voice] = True
				if self.tie_type == u"stop":
					self.tying[voice] = False

				# Staccati
				if self.chord:
					self.staccato = self.previous_staccato

			# Increment the time counter
			if note_played:
				self.time += self.duration

			# Set to "0" different values
			self.pitch_set = False
			self.duration_set = False
			self.alter = 0
			self.rest = False
			self.voice_set = False
			self.tie_type = None
			self.previous_staccato = self.staccato
			self.staccato = False
			self.chord = False
			self.harmony = False
			self.root_step_set = False
			self.kind_set = False
			self.harmony_alter = 0

		if tag == u'backup':
			if not self.duration_set:
				raise NameError("XML Duration not set for a backup")
			self.time -= self.duration
			self.duration_set = False

		if tag == u'forward':
			if not self.duration_set:
				raise NameError("XML Duration not set for a forward")
			self.time += self.duration
			self.duration_set = False
			
		if tag == u'part-name':
			self.content = u""

		if tag == u'part':    
			# compute last chord
			self.compute_chords(time_midi)

			if self.remove_silence:
				# compute initial offset to remove inital silence
				offset = min(self.note_list[0][0], self.harmony_note_list[0][0])
				logging.debug(f'[END] Removing silence - offset: {offset}')
			else:
				offset = 0

			# add melody track     
			out_midi = pretty_midi.PrettyMIDI()
			piano_program = pretty_midi.instrument_name_to_program('Acoustic grand piano')
			piano = pretty_midi.Instrument(program=piano_program)
			
			for note in self.note_list:
				pretty_midi_note = pretty_midi.Note(velocity=127, pitch=note[2], start=note[0] - offset, end=note[1] - offset)
				piano.notes.append(pretty_midi_note)

			out_midi.instruments.append(piano)

			# add harmony track
			if len(self.harmony_note_list) == 0:
				raise NameError('No harmony was detected in this file')
			else:
				piano = pretty_midi.Instrument(program=piano_program)
				
				for note in self.harmony_note_list:
					pretty_midi_note = pretty_midi.Note(velocity=127, pitch=note[2], start=note[0] - offset, end=note[1] - offset)
					piano.notes.append(pretty_midi_note)

				out_midi.instruments.append(piano)
				# write midi out
				out_midi.write(self.out_path)

				logging.debug(f'[END] Wrote out .mid at: {self.out_path}')

		return
		
	def characters(self, content):
		"""
		This callback is called when the content of a tag is found

		Parameters
		----------
		content : str
			The content of the tag
		"""

		# avoid breaklines and whitespaces
		if content.strip():
			# time and measure informations
			if self.current_element == u"divisions":
				self.division_score = int(content)
				if (not self.beat == -1) and (not self.beat_type == -1):
					self.bar_length = int(self.division_score * self.beat * 4 / self.beat_type)

			if self.current_element == u"beats":
				self.beat = int(content)

			if self.current_element == u"beat-type":
				self.beat_type = int(content)
				assert (not self.beat == -1), "beat and beat type wrong"
				assert (not self.division_score == -1), "division non defined"
				self.bar_length = int(self.division_score * self.beat * 4 / self.beat_type)

			# harmony informations
			if self.current_element == u'root-step':
				self.root_step = content
				self.root_step_set = True

			if self.current_element == u'kind':
				self.kind = content.strip()
				self.kind_set = True

			if self.current_element == u'root-alter':
				self.harmony_alter = int(content)

			# note informations
			if self.current_element == u"duration":
				self.duration = int(content)
				self.duration_set = True
				if self.rest:
					# a lot of (bad) publisher use a semibreve rest to say "rest all the bar"
					if self.duration > self.bar_length:
						self.duration = self.bar_length

			if self.current_element == u"step":
				self.step = content
				self.step_set = True

			if self.current_element == u"octave":
				self.octave = int(content)
				self.octave_set = True

			if self.current_element == u"alter":
				if content == '-':
					self.alter = -1
					logging.debug("[WARNING] Alter problem")
				else:     
					self.alter = int(content)

			if self.current_element == u"voice":
				self.current_voice = content
				self.voice_set = True

			if self.current_element == u"part-name":
				self.content += content

		return

def pre_process_file(file_path):
	"""
	Pre process MusicXML file removig DOCTYPE that would make the xml parser crash
	
	Parameters
	----------
	file_path : str
		The path to the MusicXML file

	Returns
	-------
	str
		The modified file path
	"""

	temp_file = tempfile.NamedTemporaryFile('w', suffix='.xml', prefix='tmp', delete=False, encoding='utf-8')
	
	# Remove the doctype line
	with open(file_path, 'r', encoding='utf-8') as fread:
		file_content = fread.read()

		doctype_start = file_content.find('<!DOCTYPE')
		doctype_end = doctype_start + file_content[doctype_start:].find('>') + 1
		doctype_string = file_content[doctype_start:doctype_end]

		file_content = file_content.replace(doctype_string, '')
		temp_file.write(file_content)

	temp_file_path = temp_file.name
	temp_file.close()
	
	# Return the new path
	return temp_file_path
	
def score_to_midi(score_path, out_path, verbose = True, remove_silence = True):
	"""
	Main method to convert a MusicXML score to midi
	
	Parameters
	----------
	score_path : str
		The path to the MusicXML file
	out_path : str
		The path to the out midi file
	verbose : boolean (default: True)
		if true, shows log
	remove_silence : boolean (default: True)
		if true, remove silence at the beginning of the midi file
	"""
	logging_level = logging.DEBUG
	if not verbose:
		logging_level = logging.INFO

	# logging settings
	logging.basicConfig(
		format='%(asctime)s %(levelname)-8s %(message)s',
		level=logging_level,
		datefmt='%Y-%m-%d %H:%M:%S')

	logging.debug(f'[START] Currently working on: {score_path}')

	# remove DOCTYPE
	tmp_file_path = pre_process_file(score_path)

	# get the total length in quarter notes of the track
	pre_parser = xml.sax.make_parser()
	pre_parser.setFeature(xml.sax.handler.feature_namespaces, 0)
	handler_length = TotalLengthHandler()
	pre_parser.setContentHandler(handler_length)
	pre_parser.parse(tmp_file_path)
	total_length = int(handler_length.total_length)

	# Now parse the file and get the midi
	parser = xml.sax.make_parser()
	parser.setFeature(xml.sax.handler.feature_namespaces, 0)
	Handler_score = scoreToMidiHandler(total_length, out_path, remove_silence)
	parser.setContentHandler(Handler_score)
	parser.parse(tmp_file_path)
	
	# remove temp preprocessed score file
	os.remove(tmp_file_path)

	return

if __name__ == '__main__':
	# debug only
	score_path = './examples/elise.xml'
	out_path = './examples/elise.mid'

	score_to_midi(score_path, out_path, verbose=True)
import os

from mido import MidiFile

from markov import MarkovChain
from musictheory import Key, Chord

def get_key_string(midi_file):
    meta_track = midi_file.tracks[0]
    for message in meta_track:
        if message.type == 'key_signature':
            return message.key


def get_tempo(midi_file):
    meta_track = midi_file.tracks[0]
    for message in meta_track:
        if message.type == 'set_tempo':
            return message.tempo

class ChordProgression(object):

    def __init__(self):
        self.progression = []

    def __str__(self):
        return ' | '.join([str(chord) for chord in self.progression])

    def from_midi_file(self, midi_file):
        key_string = get_key_string(midi_file)
        key = Key.from_str(key_string)

        chunks = self.__chunks(midi_file)

        for chunk in chunks:
            best_match_rate = 0
            chunk_set = set(chunk)
            for chord in key.common_chords():
                chord_set = set(chord.equivalence_classes(key))
                if chunk_set.issubset(chord_set):
                    best_match = chord
                    break
                match_rate = len(chunk_set & chord_set) / \
                             len(chunk_set | chord_set)
                if match_rate > best_match_rate:
                    best_match = chord
                    best_match_rate = match_rate
            try:
                inversion = best_match.equivalence_classes(key).index(chunk[0])
            except ValueError:
                inversion = 0 # Bass note is not a chord tone, assume root pos
            scale_degree = best_match.scale_degree
            quality = best_match.quality
            relative = best_match.relative
            self.progression.append(Chord.get_cached(scale_degree, quality,
                                                     inversion, relative))

    @staticmethod
    def __chunks(midi_file):

        def chunkify_track(bucket, midi_track, ticks_per_beat):
            index = 0
            bucket_capacity = {}
            for message in midi_track:
                if message.type == 'note_off':
                    note = message.note % 12
                    time = message.time
                    while time > 0:
                        bucket_capacity.setdefault(index, ticks_per_beat)
                        if time <= bucket_capacity[index]:
                            bucket_capacity[index] -= time
                            time = 0
                        else:
                            time -= bucket_capacity[index]
                            bucket_capacity[index] = 0
                        insert_once(note, bucket.setdefault(index, list()))
                        if bucket_capacity[index] == 0:
                            index += 1

        def insert_once(item, list_):
            if item not in list_:
                list_.append(item)

        bucket = {}

        bass_track = midi_file.tracks[4]
        tenor_track = midi_file.tracks[3]
        alto_track = midi_file.tracks[2]
        soprano_track = midi_file.tracks[1]

        for midi_track in (bass_track, tenor_track, alto_track, soprano_track):
            chunkify_track(bucket, midi_track, midi_file.ticks_per_beat)

        bucket_list = []
        for i in range(0, len(bucket)):
            bucket_list.append(bucket[i])
        return bucket_list


FILES = os.listdir('corpus/')

progressions = []
for file_ in FILES:
    if file_.endswith('.mid'):
        with MidiFile('corpus/' + file_) as midi_file:
            if len(midi_file.tracks) == 5:
                cp = ChordProgression()
                cp.from_midi_file(midi_file)
                progressions.append(cp.progression)

S = MarkovChain(progressions, order=2)
S.generate_sequence()
print('------------------------------------------------')
S.generate_sequence()
print('------------------------------------------------')
S = MarkovChain(progressions, order=3)
print('------------------------------------------------')
print('------------------------------------------------')
print('------------------------------------------------')
S.generate_sequence()
print('------------------------------------------------')
S.generate_sequence()
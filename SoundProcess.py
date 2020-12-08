from pydub import AudioSegment
from pydub.playback import play


'''
#Slicing audio file
sound = AudioSegment.from_wav(r"F:\PYTHON\battleship_game\resources\sounds\explosion1.wav")

#print(sound.duration_seconds)#3.868526077097506

newsound = sound[0:1500]

newsound.export(r"F:\PYTHON\battleship_game\resources\sounds\explosion2.wav", format="wav")
'''


sound = AudioSegment.from_wav(r"F:\PYTHON\battleship_game\resources\sounds\whoosh-sci-fi.wav")
newsound = sound[3050:3700]
newsound = newsound + 20
#faded = newsound.fade_in(500).fade_out(1000) #.fade_in(1000)
newsound.export(r"F:\PYTHON\battleship_game\resources\sounds\whoosh-sci-fi-short.wav", format="wav")


'''
sound = AudioSegment.from_wav(r"F:\PYTHON\battleship_game\resources\sounds\large-explosion.wav")
#print(sound.duration_seconds)#3.6411875
newsound = sound[:2500]
#play(newsound)
faded = newsound.fade_out(500) #.fade_in(1000)
faded.export(r"F:\PYTHON\battleship_game\resources\sounds\large-explosion-short.wav", format="wav")
print(faded.duration_seconds)
'''

'''
#Increase Volume
song = AudioSegment.from_wav(r"F:\PYTHON\battleship_game\resources\sounds\freeze.wav")

# boost volume by 6dB
louder_song = song + 20

# reduce volume by 3dB
#quieter_song = song - 3

#Play song
#play(louder_song)

#save louder song 
louder_song.export(r"F:\PYTHON\battleship_game\resources\sounds\freeze-loud.wav", format='wav')
'''

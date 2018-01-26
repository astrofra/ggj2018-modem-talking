# Load an audio file as a static sound and replay it

import os
import harfang as hg
import time
import math

hg.LoadPlugins()

plus = hg.GetPlus()
plus.RenderInit(512, 256)

# mount the system file driver
hg.MountFileDriver(hg.StdFileDriver())

scene = plus.NewScene()
cam = plus.AddCamera(scene)

# create a new sound mixer
mixer = hg.CreateMixer()
mixer.Open()
mixer.EnableSpatialization(True)

# load a sound
sound = mixer.LoadSound("assets/audio/modem_talking.ogg")
params = hg.MixerChannelState()
params.loop_mode = hg.MixerRepeat

# play the sound
channel = mixer.Start(sound, params)

emitter_distance = 10 # in meters
emitter_pos_phase = 0.0

while not plus.IsAppEnded():
	dt = hg.GetLastFrameDuration()

	emitter_pos_phase += -hg.time_to_sec_f(dt) * 0.5
	emitter_pos = hg.Vector3(emitter_distance * math.sin(emitter_pos_phase), 0, emitter_distance * math.cos(emitter_distance))

	mixer.SetChannelLocation(channel, hg.MixerChannelLocation(emitter_pos))

	plus.UpdateScene(scene)
	plus.Flip()
	plus.EndFrame()

mixer.Close()
# Load an audio file as a static sound and replay it

import os
import harfang as hg
import time
import math

vec3 = hg.Vector3
mat3 = hg.Matrix3
mat4 = hg.Matrix4
col = hg.Color

hg.LoadPlugins()

plus = hg.GetPlus()
plus.RenderInit(512, 256)

openvr_frame_renderer = hg.GetFrameRenderer("VR")
if openvr_frame_renderer.Initialize(plus.GetRenderSystem()):
	print("!! Use VR")
else:
	openvr_frame_renderer = None
	exit()
	print("!! No VR detected")

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
emitter_angle = 0.0
referentiel_pos=hg.Vector3(0, 0, 0)

scene.GetRenderableSystem().SetFrameRenderer(openvr_frame_renderer)

while not plus.IsAppEnded():
	dt = hg.GetLastFrameDuration()

	input_system = hg.GetInputSystem()
	head_controller = input_system.GetDevice("HMD")	

	if head_controller is not None:
		mat_head = head_controller.GetMatrix(hg.InputDeviceMatrixHead)

	# emitter_angle += -hg.time_to_sec_f(dt) * 0.5
	emitter_angle = mat_head.GetRotation().y
	emitter_pos = hg.Vector3(emitter_distance * math.sin(emitter_angle), 0, emitter_distance * math.cos(emitter_angle))
	print(emitter_angle)

	mixer.SetChannelLocation(channel, hg.MixerChannelLocation(emitter_pos))

	plus.UpdateScene(scene)
	plus.Flip()
	plus.EndFrame()

mixer.Close()
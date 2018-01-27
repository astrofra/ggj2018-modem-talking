# Load an audio file as a static sound and replay it

import os
import harfang as hg
import time
import math
import random

enable_vr = True

vec3 = hg.Vector3
mat3 = hg.Matrix3
mat4 = hg.Matrix4
col = hg.Color

hg.LoadPlugins()

plus = hg.GetPlus()
plus.RenderInit(512, 256)

if enable_vr:
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

timer = 0.0
current_tower = 0
channel_tower = -1
dispatch = None
word_list = []
current_word = 0
game_state = "waiting"


def wait_player_start():
	global game_state, dispatch
	if timer > 2.5:
		game_state = "announcement"
		dispatch = tower_announce


def tower_announce():
	global dispatch, current_tower, word_list, current_word
	current_tower += 1
	if current_tower > 2:
		current_tower = 0

	word_list = []
	word_list.append("hello_i_am_number_" + str(current_tower))
	word_list.append("i_repeat")
	word_list.append("number_" + str(current_tower))
	current_word = 0

	dispatch = unroll_word_list


def unroll_word_list():
	global dispatch, channel_tower, mixer, current_word, game_state, word_list

	if channel_tower is None or mixer.GetPlayState(channel_tower) == hg.MixerStopped:
		if current_word < len(word_list):
			new_sound = mixer.LoadSound("assets/audio/" + word_list[current_word] + ".wav")
			channel_tower = mixer.Start(new_sound)
			current_word += 1
		else:
			channel_tower = None
			if game_state == "announcement":
				game_state = "challenge"
				dispatch = create_challenge
			elif game_state == "challenge":
				game_state = "announcement"
				dispatch = tower_announce


def speaking_is_over():
	global dispatch, channel_tower
	dispatch = None
	channel_tower = None


def create_challenge():
	global dispatch, timer, word_list, current_word
	timer = 0.0
	current_word = 0
	a = int(random.uniform(0, 9))
	b = int(random.uniform(0, 9))
	sign = "number_plus"
	if random.uniform(0, 100) > 50:
		sign = "number_by"

	word_list = []
	word_list.append("number_" + str(a))
	word_list.append(sign)
	word_list.append("number_" + str(b))
	word_list.append("number_equals")

	dispatch = unroll_word_list

# Main loop

if enable_vr:
	scene.GetRenderableSystem().SetFrameRenderer(openvr_frame_renderer)

dispatch = wait_player_start

while not plus.IsAppEnded():
	dt = hg.GetLastFrameDuration()

	input_system = hg.GetInputSystem()
	if enable_vr:
		head_controller = input_system.GetDevice("HMD")
	else:
		head_controller = None

	if head_controller is not None:
		mat_head = head_controller.GetMatrix(hg.InputDeviceMatrixHead)
	else:
		mat_head = mat4()

	# emitter_angle += -hg.time_to_sec_f(dt) * 0.5
	emitter_angle = mat_head.GetRotation().y
	emitter_pos = hg.Vector3(emitter_distance * math.sin(emitter_angle), 0, emitter_distance * math.cos(emitter_angle))
	# print(emitter_angle)
	plus.Text2D(16, 16, "emitter_angle = " + str(emitter_angle))
	plus.Text2D(16, 32, "timer         = " + str(timer))
	plus.Text2D(16, 48, "game_state    = " + game_state)
	if len(word_list) > 0 and current_word < len(word_list):
		plus.Text2D(16, 64, "current word = " + word_list[max(0, current_word - 1)])
		plus.Text2D(16, 64 + 16, "next word = " + word_list[current_word])

	mixer.SetChannelLocation(channel, hg.MixerChannelLocation(emitter_pos))
	if channel_tower is not None:
		mixer.SetChannelLocation(channel_tower, hg.MixerChannelLocation(emitter_pos))

	if dispatch is not None:
		dispatch()

	timer += hg.time_to_sec_f(dt)

	plus.UpdateScene(scene)
	plus.Flip()
	plus.EndFrame()

mixer.Close()
# Load an audio file as a static sound and replay it

import os
import harfang as hg
import time
import math
import random

enable_vr = False

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

game_device = hg.GetInputSystem().GetDevice("xinput.port0")

scene = plus.NewScene()
cam = plus.AddCamera(scene)

plus.AddLight(scene, hg.Matrix4.TranslationMatrix(hg.Vector3(0, 20, -7)), hg.LightModelPoint)
# plus.AddSphere(scene, hg.Matrix4.TranslationMatrix(hg.Vector3(0, 0.5, -10)))
# plus.AddPhysicPlane(scene, hg.Matrix4.TranslationMatrix(hg.Vector3(0, -2, 0)))

# create a new sound mixer
mixer = hg.CreateMixer()
mixer.Open()
mixer.EnableSpatialization(True)

channel = None
# load & play a bg sound
sound = mixer.LoadSound("assets/audio/modem_talking.ogg")
params = hg.MixerChannelState()
params.loop_mode = hg.MixerRepeat
params.volume = 0.15
channel = mixer.Start(sound, params)
print("channel = " + str(channel))

# load & play a tone sound
sound = mixer.LoadSound("assets/audio/tone.wav")
params = hg.MixerChannelState()
params.loop_mode = hg.MixerRepeat
params.volume = 0.0
tone_channel = mixer.Start(sound, params)
print("tone_channel = " + str(tone_channel))


emitter_distance = 10 # in meters
emitter_angle = 0.0
referentiel_pos = hg.Vector3(0, 0, 0)

timer = 0.0
current_tower = 0
channel_tower = -1
dispatch = None
word_list = []
current_word = 0
game_state = "waiting"
emitter_pos = vec3(0,0,0)
tower_target = -1
shooting = False


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
	word_list.append("pause")
	word_list.append("i_repeat")
	word_list.append("tower")
	word_list.append("number_" + str(current_tower))
	word_list.append("pause")
	word_list.append("pause")

	current_word = 0

	dispatch = unroll_word_list


def unroll_word_list():
	global dispatch, channel_tower, mixer, current_word, game_state, word_list, emitter_pos

	if channel_tower is None or mixer.GetPlayState(channel_tower) == hg.MixerStopped:
		if current_word < len(word_list):
			new_sound = mixer.LoadSound("assets/audio/" + word_list[current_word] + ".wav")
			new_pos_params = hg.MixerChannelLocation(emitter_pos)
			channel_tower = mixer.Start(new_sound, new_pos_params)
			print("channel_tower = " + str(channel_tower))
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
	global dispatch, timer, word_list, current_word, tower_target
	timer = 0.0
	current_word = 0
	a = int(random.uniform(0, 9))
	b = int(random.uniform(0, 9))
	tower_target = -1
	while tower_target < 0 or tower_target == current_tower:
		tower_target = int(random.uniform(0, 2))

	sign = "number_plus"
	if random.uniform(0, 100) > 50:
		sign = "number_by"

	word_list = []
	word_list.append("pause")
	word_list.append("this_is_the_transmission")
	word_list.append("pause")
	word_list.append("pause")
	word_list.append("number_" + str(a))
	word_list.append(sign)
	word_list.append("number_" + str(b))
	word_list.append("number_equals")
	word_list.append("pause")
	word_list.append("please_transmit_to")
	word_list.append("tower")
	word_list.append("number_" + str(tower_target))
	word_list.append("pause")
	word_list.append("i_repeat")
	word_list.append("please_transmit_to")
	word_list.append("tower")
	word_list.append("number_" + str(tower_target))
	word_list.append("pause")

	dispatch = unroll_word_list


def emit_controller():
	global shooting, tone_channel
	if not game_device.WasButtonPressed(hg.Button0) and game_device.IsButtonDown(hg.Button0):
		shooting = True
	else:
		shooting = False


def update_tone_sound(dt):
	global shooting, tone_channel
	vol = max(0.0, mixer.GetChannelState(tone_channel).volume - 15.0 * hg.time_to_sec_f(dt))
	if shooting:
		vol = min(1.0, mixer.GetChannelState(tone_channel).volume + 10.0 * hg.time_to_sec_f(dt))

	mixer.SetChannelState(tone_channel, hg.MixerChannelState(0, vol * 0.5, hg.MixerRepeat))


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
	emitter_angle = mat_head.GetRotation().y + (current_tower * 2 * math.pi / 3.0)
	emitter_pos = hg.Vector3(emitter_distance * math.sin(emitter_angle), 0, emitter_distance * math.cos(emitter_angle))
	# print(emitter_angle)
	plus.Text2D(16, 16, "emitter_angle = " + str(math.radians(emitter_angle)))
	plus.Text2D(16, 32, "timer         = " + str(timer))
	plus.Text2D(16, 48, "game_state    = " + game_state)
	plus.Text2D(16, 64, "shooting      = " + str(shooting))
	if len(word_list) > 0 and current_word < len(word_list):
		plus.Text2D(16, 64 + 16, "current word = " + word_list[max(0, current_word - 1)])
		plus.Text2D(16, 64 + 32, "next word = " + word_list[current_word])

	if channel is not None:
		mixer.SetChannelLocation(channel, hg.MixerChannelLocation(emitter_pos))

	if dispatch is not None:
		dispatch()

	if channel_tower is not None:
		mixer.SetChannelLocation(channel_tower, hg.MixerChannelLocation(emitter_pos))

	emit_controller()
	update_tone_sound(dt)

	timer += hg.time_to_sec_f(dt)

	plus.UpdateScene(scene)
	plus.Flip()
	plus.EndFrame()

mixer.Close()
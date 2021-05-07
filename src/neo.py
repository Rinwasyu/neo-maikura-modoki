#
# Copyright 2021 Rinwasyu
# 
# This file is part of neo-maikura-modoki.
# 
# Neo-maikura-modoki is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Neo-maikura-modoki is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
# 

import glfw
from OpenGL.GL import *
import numpy as np
import math

window_config = {
	"width": 800,
	"height": 800,
}

world_config = {
	"width": 20,
	"height": 20,
	"depth": 20,
	"block_size": 1,
}

is_world_updated = False

def loadFile(file_path):
	with open(file_path, "rb") as f:
		return f.read()

def printCompilerInfoLog(shader):
	print("log:", glGetShaderInfoLog(shader))

def createProgram(vertex_shader_path, fragment_shader_path):
	program = glCreateProgram()
	
	vertex_shader_src = loadFile(vertex_shader_path)
	vertex_shader = glCreateShader(GL_VERTEX_SHADER)
	glShaderSource(vertex_shader, vertex_shader_src)
	glCompileShader(vertex_shader)
	printCompilerInfoLog(vertex_shader)
	glAttachShader(program, vertex_shader)
	glDeleteShader(vertex_shader)	
	
	fragment_shader_src = loadFile(fragment_shader_path)
	fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
	glShaderSource(fragment_shader, fragment_shader_src)
	glCompileShader(fragment_shader)
	printCompilerInfoLog(fragment_shader)
	glAttachShader(program, fragment_shader)
	glDeleteShader(fragment_shader)
	
	glLinkProgram(program)
	
	return program

def createTextureFromPPMFile(file_path):
	texture = glGenTextures(1)
	glActiveTexture(GL_TEXTURE0)
	glBindTexture(GL_TEXTURE_2D, texture)
	
	pnm_data = loadFile(file_path)
	
	# 4-bytes alignment
	cnt_lf = 0
	for i in range(len(pnm_data)):
		if pnm_data[i] == ord('\n'):
			cnt_lf += 1
			if cnt_lf == 4:
				break
	image_data = bytearray(pnm_data[i+1:])
	
	texture_width = 8
	texture_height = 8
	glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, texture_width, texture_height, 0, GL_RGB, GL_UNSIGNED_BYTE, image_data)
	glGenerateMipmap(GL_TEXTURE_2D)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
	glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
	
	return

class Player:
	def __init__(self, x, y, z, rx, ry):
		self.x = x
		self.y = y
		self.z = z
		self.vx = 0
		self.vy = 0
		self.vz = 0
		self.speed = 0.01
		self.rx = rx
		self.ry = ry
		self.hand_anim = 0
		self.radius = 0.15
		self.height = 1.9
		self.eyeshot = 10
		self.holding = 1
	
	def tick(self):
		global keystat
		
		self.vx *= 0.5
		self.vz *= 0.5
		diff_sin_ry = self.speed * math.sin(self.ry*math.pi/180)
		diff_cos_ry = self.speed * math.cos(self.ry*math.pi/180)
		if keystat.FORWARD:
			self.vx += diff_sin_ry
			self.vz -= diff_cos_ry
		if keystat.BACK:
			self.vx -= diff_sin_ry
			self.vz += diff_cos_ry
		if keystat.LEFT:
			self.vx -= diff_cos_ry
			self.vz -= diff_sin_ry
		if keystat.RIGHT:
			self.vx += diff_cos_ry
			self.vz += diff_sin_ry
		if keystat.JUMP:
			self.vy = 0.025
			keystat.JUMP = False
		else:
			self.vy -= 0.0003
		if keystat.LAND:
			if self.vy > 0:
				self.vy *= -1
			self.vy -= 0.001
		
		if self.hand_anim > 0:
			self.hand_anim -= 1
		if mousestat.LEFT:
			if self.hand_anim == 0:
				remove_block()
				self.hand_anim = 45
		elif mousestat.RIGHT:
			if self.hand_anim == 0:
				create_block()
				self.hand_anim = 45
		
		next_x = self.x + self.vx
		next_y = self.y + self.vy
		next_z = self.z + self.vz
		if next_x - self.radius < 0 or next_x + self.radius >= world_config["width"]:
			self.vx = 0
			next_x = self.x
		if next_y < 0 or next_y + self.height >= world_config["height"]:
			self.vy = 0
			next_y = self.y
		if next_z - self.radius < 0 or next_z + self.radius >= world_config["depth"]:
			self.vz = 0
			next_z = self.z
		
		radius = (-self.radius, self.radius)
		height = (0, 1, self.height)
		for i in radius:
			for j in height:
				for k in radius:
					if block[int(next_x + i)][int(self.y + j)][int(self.z + k)] > 0:
						self.vx = 0
						next_x = self.x
		for i in radius:
			for j in height:
				for k in radius:
					if block[int(next_x + i)][int(next_y + j)][int(self.z + k)] > 0:
						self.vy = 0
						next_y = self.y
		for i in radius:
			for j in height:
				for k in radius:
					if block[int(next_x + i)][int(next_y + j)][int(next_z + k)] > 0:
						self.vz = 0
						next_z = self.z
		
		self.x += self.vx
		self.y += self.vy
		self.z += self.vz

class Keystat:
	def __init__(self):
		self.FORWARD = False
		self.BACK = False
		self.LEFT = False
		self.RIGHT = False
		self.JUMP = False
		self.LAND = False

class Mousestat:
	def __init__(self):
		self.RIGHT = False
		self.LEFT = False
		self.x = -1
		self.y = -1

def key_callback(window, key, scancode, action, mod):
	global keystat, player
	if action == glfw.PRESS:
		if key == glfw.KEY_UP or key == glfw.KEY_W:
			keystat.FORWARD = True
		elif key == glfw.KEY_DOWN or key == glfw.KEY_S:
			keystat.BACK = True
		elif key == glfw.KEY_LEFT or key == glfw.KEY_A:
			keystat.LEFT = True
		elif key == glfw.KEY_RIGHT or key == glfw.KEY_D:
			keystat.RIGHT = True
		elif key == glfw.KEY_SPACE:
			keystat.JUMP = True
		elif key == glfw.KEY_LEFT_SHIFT:
			keystat.LAND = True
		elif key == glfw.KEY_P: # For debugging
			print("player  x:{},y:{},z:{},rx:{},ry:{}".format(
						int(player.x), int(player.y), int(player.z), int(player.rx), int(player.ry)
					)
				)
		elif key == glfw.KEY_R:
			# recreate the world
			new_world()
		elif key == glfw.KEY_ESCAPE: # show mouse cursor
			cursor_x = -1
			cursor_y = -1
			glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_NORMAL)
		elif key == glfw.KEY_Q: # close window
			glfw.set_window_should_close(window, GL_TRUE)
		elif key == glfw.KEY_1:
			player.holding = 1
		elif key == glfw.KEY_2:
			player.holding = 2
		elif key == glfw.KEY_3:
			player.holding = 3
		elif key == glfw.KEY_4:
			player.holding = 4
		elif key == glfw.KEY_5:
			player.holding = 5
		elif key == glfw.KEY_6:
			player.holding = 6
		elif key == glfw.KEY_7:
			player.holding = 7
		elif key == glfw.KEY_8:
			player.holding = 8
		elif key == glfw.KEY_9:
			player.holding = 9
	elif action == glfw.RELEASE:
		if key == glfw.KEY_UP or key == glfw.KEY_W:
			keystat.FORWARD = False
		elif key == glfw.KEY_DOWN or key == glfw.KEY_S:
			keystat.BACK = False
		elif key == glfw.KEY_LEFT or key == glfw.KEY_A:
			keystat.LEFT = False
		elif key == glfw.KEY_RIGHT or key == glfw.KEY_D:
			keystat.RIGHT = False
		elif key == glfw.KEY_SPACE:
			keystat.JUMP = False
		elif key == glfw.KEY_LEFT_SHIFT:
			keystat.LAND = False
	return

def cursor_pos_callback(window, xpos, ypos):
	global player, mousestat
	if mousestat.x != -1:
		if abs(player.rx + (ypos - mousestat.y) * 0.5) <= 90:
			player.rx += (ypos - mousestat.y) * 0.5
		player.ry = (player.ry + (xpos - mousestat.x) * 0.5 + 360) % 360
	mousestat.x = xpos
	mousestat.y = ypos
	return

def mouse_button_callback(window, button, action, mods):
	global mousestat
	if glfw.get_input_mode(window, glfw.CURSOR) == glfw.CURSOR_NORMAL:
		print("hide mouse cursor")
		glfw.set_input_mode(window, glfw.CURSOR, glfw.CURSOR_DISABLED) # hide mouse cursor
		return
	if action == glfw.PRESS:
		if button == glfw.MOUSE_BUTTON_LEFT:
			mousestat.LEFT = True
		elif button == glfw.MOUSE_BUTTON_RIGHT:
			mousestat.RIGHT = True
	elif action == glfw.RELEASE:
		if button == glfw.MOUSE_BUTTON_LEFT:
			mousestat.LEFT = False
		elif button == glfw.MOUSE_BUTTON_RIGHT:
			mousestat.RIGHT = False
	return

def create_block():
	global block, is_world_updated
	x = player.x
	y = player.y + player.height*0.9
	z = player.z
	step = 0.01
	diff_x = math.sin(player.ry*math.pi/180) * math.cos(player.rx*math.pi/180) * step
	diff_y = -math.sin(player.rx*math.pi/180) * step
	diff_z = -math.cos(player.ry*math.pi/180) * math.cos(player.rx*math.pi/180) * step
	distance = 0
	while distance <= player.eyeshot:
		distance += step
		bx = x
		by = y
		bz = z
		x += diff_x
		y += diff_y
		z += diff_z
		if x-player.radius < 0 or x+player.radius >= world_config["width"]\
				or y < 0 or y >= world_config["height"]\
				or z-player.radius < 0 or z+player.radius >= world_config["depth"]:
			return
		if block[int(x)][int(y)][int(z)] > 0:
			if abs(int(x)+0.5 - bx) < abs(int(z)+0.5 - bz):
				bx = x
			else:
				bz = z
			if (int(player.x-player.radius) == int(bx) or int(player.x+player.radius) == int(bx))\
					and int(int(by)-player.y) < player.height and int(int(by)-player.y) >= 0\
					and (int(player.z-player.radius) == int(bz) or int(player.z+player.radius) == int(bz)):
				return
			else:
				block[int(bx)][int(by)][int(bz)] = player.holding
				update_brightness(int(bx), int(by), int(bz), True)
				print("created! (", int(bx), ",", int(by), ",", int(bz), ")")
				is_world_updated = True
				#add_block_visibility(int(bx), int(by), int(bz), -1)
			return

def remove_block():
	global block, is_world_updated
	x = player.x
	y = player.y + player.height*0.9
	z = player.z
	step = 0.01
	diff_x = math.sin(player.ry*math.pi/180) * math.cos(player.rx*math.pi/180) * step
	diff_y = -math.sin(player.rx*math.pi/180) * step
	diff_z = -math.cos(player.ry*math.pi/180) * math.cos(player.rx*math.pi/180) * step
	distance = 0
	while distance <= player.eyeshot:
		distance += step
		x += diff_x
		y += diff_y
		z += diff_z
		if x < 0 or x >= world_config["width"] or y < 0 or y >= world_config["height"] or z < 0 or z >= world_config["depth"]:
			return
		if block[int(x)][int(y)][int(z)] > 0:
			block[int(x)][int(y)][int(z)] = 0
			update_brightness(int(x), int(y), int(z), False)
			print("removed (", int(x), ",", int(y), ",", int(z), ")")
			is_world_updated = True
			return

def update_brightness(x:int, y:int, z:int, is_block_created:bool):
	#print("update_brightness x:{}, y:{}, z:{}".format(x, y, z))
	global block_brightness, space_brightness
	space_offset = []
	for tmp_x in [-1, 0, 1]:
		for tmp_y in [-1, 0, 1]:
			for tmp_z in [-1, 0, 1]:
				if tmp_x != 0 or tmp_y != 0 or tmp_z != 0:
					space_offset.append([tmp_x, tmp_y, tmp_z])
	voxel_offset = [
			[0, 0, 1], [-1, 0, 0], [0, 1, 0], [1, 0, 0], [0, -1, 0], [0, 0, -1]
		]
	surface_index = [
			[5], [3], [4], [1],  [2], [0]
		]
	if is_block_created:
		space_brightness_1 = 0
		space_brightness_2 = 0
		for i in range(len(space_offset)):
			if x+space_offset[i][0] < 0 or x+space_offset[i][0] >= world_config["width"] or \
					y+space_offset[i][1] < 0 or y+space_offset[i][1] >= world_config["height"] or \
					z+space_offset[i][2] < 0 or z+space_offset[i][2] >= world_config["depth"]:
				continue
			space_brightness_2 = max(space_brightness_2, min(space_brightness_1, space_brightness[x+space_offset[i][0]][y+space_offset[i][1]][z+space_offset[i][2]]))
			space_brightness_1 = max(space_brightness_1, space_brightness[x+space_offset[i][0]][y+space_offset[i][1]][z+space_offset[i][2]])
		space_brightness[x][y][z] = (space_brightness_1*1.5 + space_brightness_2*0.5) / 2
		for i in range(6):
			block_brightness[x][y][z][i] = space_brightness[x][y][z]
		for i in range(len(voxel_offset)):
			if x+voxel_offset[i][0] < 0 or x+voxel_offset[i][0] >= world_config["width"] or \
					y+voxel_offset[i][1] < 0 or y+voxel_offset[i][1] >= world_config["height"] or \
					z+voxel_offset[i][2] < 0 or z+voxel_offset[i][2] >= world_config["depth"]:
				continue
			for j in range(len(surface_index[i])):
				if block_brightness[x+voxel_offset[i][0]][y+voxel_offset[i][1]][z+voxel_offset[i][2]][surface_index[i][j]] != -1:
					block_brightness[x+voxel_offset[i][0]][y+voxel_offset[i][1]][z+voxel_offset[i][2]][surface_index[i][j]] = 0
			for j in range(len(voxel_offset)):
				if x+voxel_offset[j][0] < 0 or x+voxel_offset[j][0] >= world_config["width"] or \
						y+voxel_offset[j][1] < 0 or y+voxel_offset[j][1] >= world_config["height"] or \
						z+voxel_offset[j][2] < 0 or z+voxel_offset[j][2] >= world_config["depth"]:
					continue
				
	else:
		for i in range(6):
			block_brightness[x][y][z][i] = -1
		space_brightness_1 = 0
		space_brightness_2 = 0
		for i in range(len(space_offset)):
			if x+space_offset[i][0] < 0 or x+space_offset[i][0] >= world_config["width"] or \
					y+space_offset[i][1] < 0 or y+space_offset[i][1] >= world_config["height"] or \
					z+space_offset[i][2] < 0 or z+space_offset[i][2] >= world_config["depth"]:
				continue
			space_brightness_2 = max(space_brightness_2, min(space_brightness_1, space_brightness[x+space_offset[i][0]][y+space_offset[i][1]][z+space_offset[i][2]]))
			space_brightness_1 = max(space_brightness_1, space_brightness[x+space_offset[i][0]][y+space_offset[i][1]][z+space_offset[i][2]])
		space_brightness[x][y][z] = (space_brightness_1*1.5 + space_brightness_2*0.5) / 2
		for i in range(len(voxel_offset)):
			if x+voxel_offset[i][0] < 0 or x+voxel_offset[i][0] >= world_config["width"] or \
					y+voxel_offset[i][1] < 0 or y+voxel_offset[i][1] >= world_config["height"] or \
					z+voxel_offset[i][2] < 0 or z+voxel_offset[i][2] >= world_config["depth"]:
				continue
			for j in range(len(surface_index[i])):
				if block_brightness[x+voxel_offset[i][0]][y+voxel_offset[i][1]][z+voxel_offset[i][2]][surface_index[i][j]] != -1:
					block_brightness[x+voxel_offset[i][0]][y+voxel_offset[i][1]][z+voxel_offset[i][2]][surface_index[i][j]] = space_brightness[x][y][z]

def create_world(width, height, depth):
	global block, block_brightness, space_brightness
	block = [[[0] * depth for i in range(height)] for j in range(width)]
	block_brightness = [[[[-1] * 24 for i in range(depth)] for j in range(height)] for k in range(width)]
	space_brightness = [[[1] * depth for i in range(height)] for j in range(width)]
	for i in range(width):
		for j in range(10):
			for k in range(depth):
				block[i][j][k] = 1
				for l in range(6):
					block_brightness[i][j][k][l] = 0
				if j == 9:
					block_brightness[i][j][k][2] = 1
				space_brightness[i][j][k] = 0
	return

def init_game():
	print("initializing game...")
	global keystat, mousestat, player
	keystat = Keystat()
	mousestat = Mousestat()
	player = Player(15, 10, 15, 0, 0)
	create_world(world_config["width"], world_config["height"], world_config["depth"])

def get_voxels_vertices():
	width = world_config["width"]
	height = world_config["height"]
	depth = world_config["depth"]
	vertices = []
	for i in range(width):
		for j in range(height):
			for k in range(depth):
				vertices.append([
						(-0.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (1.0+k)*world_config["block_size"], 1.0,
						
						(-0.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(-0.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (-0.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
						(1.0+i)*world_config["block_size"], (1.0+j)*world_config["block_size"], (-0.0+k)*world_config["block_size"], 1.0,
					])
	return vertices

def get_voxels_indices():
	width = world_config["width"]
	height = world_config["height"]
	depth = world_config["depth"]
	indices = []
	for i in range(width):
		for j in range(height):
			for k in range(depth):
				indices.append([
						0+(i*height*depth+j*depth+k)*24, 3+(i*height*depth+j*depth+k)*24, 6+(i*height*depth+j*depth+k)*24, # 手前 0-1-2, 2-3-0
						6+(i*height*depth+j*depth+k)*24, 9+(i*height*depth+j*depth+k)*24, 0+(i*height*depth+j*depth+k)*24,
						1+(i*height*depth+j*depth+k)*24, 12+(i*height*depth+j*depth+k)*24, 15+(i*height*depth+j*depth+k)*24, # 左側 0-4-5, 5-1-0
						15+(i*height*depth+j*depth+k)*24, 4+(i*height*depth+j*depth+k)*24, 1+(i*height*depth+j*depth+k)*24,
						2+(i*height*depth+j*depth+k)*24, 10+(i*height*depth+j*depth+k)*24, 21+(i*height*depth+j*depth+k)*24, # 上側 0-3-7, 7-4-0
						21+(i*height*depth+j*depth+k)*24, 13+(i*height*depth+j*depth+k)*24, 2+(i*height*depth+j*depth+k)*24,
						11+(i*height*depth+j*depth+k)*24, 7+(i*height*depth+j*depth+k)*24, 18+(i*height*depth+j*depth+k)*24, # 右側 3-2-6, 6-7-3
						18+(i*height*depth+j*depth+k)*24, 22+(i*height*depth+j*depth+k)*24, 11+(i*height*depth+j*depth+k)*24,
						5+(i*height*depth+j*depth+k)*24, 16+(i*height*depth+j*depth+k)*24, 19+(i*height*depth+j*depth+k)*24, # 下側 1-5-6, 6-2-1
						19+(i*height*depth+j*depth+k)*24, 8+(i*height*depth+j*depth+k)*24, 5+(i*height*depth+j*depth+k)*24,
						14+(i*height*depth+j*depth+k)*24, 23+(i*height*depth+j*depth+k)*24, 20+(i*height*depth+j*depth+k)*24, # 奥側 4-7-6, 6-5-4
						20+(i*height*depth+j*depth+k)*24, 17+(i*height*depth+j*depth+k)*24, 14+(i*height*depth+j*depth+k)*24
					])
	return indices

def get_voxels_texture_coords():
	width = world_config["width"]
	height = world_config["height"]
	depth = world_config["depth"]
	texture_coords = []
	for i in range(width):
		for j in range(height):
			for k in range(depth):
				texture_coords.append([
						0.0, 0.0, # 0
						0.0, 0.0, # 1
						0.0, 0.0, # 2
						0.0, 1.0, # 3
						1.0, 0.0, # 4
						0.0, 0.0, # 5
						1.0, 1.0, # 6
						0.0, 1.0, # 7
						1.0, 0.0, # 8
						1.0, 0.0, # 9
						0.0, 1.0, # 10
						0.0, 0.0, # 11
						0.0, 1.0, # 12
						1.0, 0.0, # 13
						0.0, 0.0, # 14
						1.0, 1.0, # 15
						0.0, 1.0, # 16
						1.0, 0.0, # 17
						1.0, 1.0, # 18
						1.0, 1.0, # 19
						1.0, 1.0, # 20
						1.0, 1.0, # 21
						1.0, 0.0, # 22
						0.0, 1.0, # 23
					])
	return texture_coords

def get_voxels_brightness():
	width = world_config["width"]
	height = world_config["height"]
	depth = world_config["depth"]
	brightness = []
	for i in range(width):
		for j in range(height):
			for k in range(depth):
				for l in range(6):
					brightness.append([
							block_brightness[i][j][k][l]
						])
	return brightness

def create_voxels_vao():
	vao = glGenVertexArrays(1)
	glBindVertexArray(vao)		
	
	vertices = np.array(get_voxels_vertices(), dtype=np.float32)
	indices = np.array(get_voxels_indices(), dtype=np.uint32)
	texture_coords = np.array(get_voxels_texture_coords(), dtype=np.float32)
	brightness = np.array(get_voxels_brightness(), dtype=np.float32)
	
	glEnableVertexAttribArray(0)
	vbo = glGenBuffers(1)
	glBindBuffer(GL_ARRAY_BUFFER, vbo)
	glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_DYNAMIC_DRAW)
	glVertexAttribPointer(0, 4, GL_FLOAT, GL_FALSE, 0, None)
	
	ebo = glGenBuffers(1)
	glBindBuffer(GL_ELEMENT_ARRAY_BUFFER, ebo)
	glBufferData(GL_ELEMENT_ARRAY_BUFFER, indices.nbytes, indices, GL_DYNAMIC_DRAW)
	
	glEnableVertexAttribArray(1)
	createTextureFromPPMFile("images/plants_8x8.ppm")
	texture_vbo = glGenBuffers(1)
	glBindBuffer(GL_ARRAY_BUFFER, texture_vbo)
	glBufferData(GL_ARRAY_BUFFER, texture_coords.nbytes, texture_coords, GL_DYNAMIC_DRAW)
	glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 0, None)
	
	brightness_ssbo = glGenBuffers(1)
	glBindBuffer(GL_SHADER_STORAGE_BUFFER, brightness_ssbo)
	glBufferData(GL_SHADER_STORAGE_BUFFER, brightness.nbytes, brightness, GL_DYNAMIC_DRAW)
	glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, brightness_ssbo)
	glBindBuffer(GL_SHADER_STORAGE_BUFFER, 0)
	
	glBindBuffer(GL_ARRAY_BUFFER, 0)
	
	glBindVertexArray(0)
	
	return (vao, vbo, ebo, texture_vbo, brightness_ssbo)

def draw_voxels(program, vao):
	glUseProgram(program)
	glBindVertexArray(vao)
	
	glUniform3f(glGetUniformLocation(program, "eye_xyz"), player.x*world_config["block_size"], (player.y+player.height*0.9)*world_config["block_size"], player.z*world_config["block_size"])
	glUniform1f(glGetUniformLocation(program, "eye_rx"), player.rx/180*math.pi)
	glUniform1f(glGetUniformLocation(program, "eye_ry"), -player.ry/180*math.pi)
	glDrawElements(GL_TRIANGLES, world_config["width"]*world_config["height"]*world_config["depth"]*36, GL_UNSIGNED_INT, None)
	
	return

def update_brightness_ssbo(brightness_ssbo):
	glBindBuffer(GL_SHADER_STORAGE_BUFFER, brightness_ssbo)
	
	brightness = np.array(get_voxels_brightness(), dtype=np.float32)
	
	# update all brightness data
	glBufferData(GL_SHADER_STORAGE_BUFFER, brightness.nbytes, brightness, GL_DYNAMIC_DRAW)
	
	glBindBufferBase(GL_SHADER_STORAGE_BUFFER, 0, brightness_ssbo)
	
	return

def main():
	# initialize glfw
	if not glfw.init():
		return
	
	# use OpenGL 4.6 core profile
	glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
	glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 6)
	glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
	
	# enable dobble-buffer
	glfw.window_hint(glfw.DOUBLEBUFFER, glfw.TRUE)
	
	# create an application window
	window = glfw.create_window(window_config["width"], window_config["height"], "neo-maikura-modoki", None, None)
	if not window:
		glfw.terminate()
		return
	
	# make context
	glfw.make_context_current(window)
	
	# set viewport
	glViewport(0, 0, window_config["width"], window_config["height"])
	
	# initialize game
	init_game()
	
	# set callbacks
	glfw.set_key_callback(window, key_callback)
	glfw.set_cursor_pos_callback(window, cursor_pos_callback)
	glfw.set_mouse_button_callback(window, mouse_button_callback)
	
	# compile and link shaders
	voxels_program = createProgram("shaders/voxel.vert", "shaders/voxel.frag")
	
	# create vao, vbo, ebo and ssbo
	(voxels_vao, voxels_vbo, voxels_ebo, texture_vbo, brightness_ssbo) = create_voxels_vao()
	
	# clear
	glClearColor(0.6, 0.8, 1, 1)
	
	# enable depth-test and culling
	glEnable(GL_DEPTH_TEST)
	glEnable(GL_CULL_FACE)
	
	# enable blending
	glEnable(GL_BLEND)
	glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
	
	# fps
	fps = 0
	last_time = glfw.get_time()
	
	global is_world_updated
	# main loop
	while not glfw.window_should_close(window):
		glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
		
		# draw voxels
		draw_voxels(voxels_program, voxels_vao)
		
		player.tick()
		
		if is_world_updated:
			update_brightness_ssbo(brightness_ssbo)
			is_world_updated = False
		
		glfw.swap_buffers(window)
		glfw.wait_events_timeout(1e-2)
		
		# calculate fps
		current_time = glfw.get_time()
		if current_time - last_time > 1:
			print("fps:", fps)
			last_time = current_time
			fps = 0
		fps = fps + 1
	
	glfw.terminate()


if __name__ == "__main__":
	main()
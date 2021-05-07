/*
 * Copyright 2021 Rinwasyu
 * 
 * This file is part of neo-maikura-modoki.
 * 
 * Neo-maikura-modoki is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * Neo-maikura-modoki is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 * 
 */

#version 460 core

layout(location=0) in vec4 position;
layout(location=1) in vec2 vertex_uv;

uniform vec3 eye_xyz;
uniform float eye_rx;
uniform float eye_ry;

out vec2 uv;

void main(void) {
	mat4 view_translation = mat4(
		1, 0, 0, 0,
		0, 1, 0, 0,
		0, 0, 1, 0,
		-eye_xyz[0], -eye_xyz[1], -eye_xyz[2], 1
	);
	mat4 view_x_rotation = mat4(
		1, 0, 0, 0,
		0, cos(eye_rx), sin(eye_rx), 0,
		0, -sin(eye_rx), cos(eye_rx), 0,
		0, 0, 0, 1
	);
	mat4 view_y_rotation = mat4(
		cos(eye_ry), 0, sin(eye_ry), 0,
		0, 1, 0, 0,
		-sin(eye_ry), 0, cos(eye_ry), 0,
		0, 0, 0, 1
	);
	
	float l = -0.08, r = 0.08, t = 0.08, b = -0.08, n = 0.1, f = 100;
	mat4 perspective_projection = mat4(
		2*n/(r-l), 0, 0, 0,
		0, 2*n/(t-b), 0, 0,
		(r+l)/(r-l), (t+b)/(t-b), -(f+n)/(f-n), -1,
		0, 0, -2*n*f/(f-n), 0
	);
	gl_Position = perspective_projection * view_x_rotation * view_y_rotation * view_translation * position;
	
	uv = vertex_uv;
}
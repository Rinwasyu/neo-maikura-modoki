/*
 * Copyright 2021,2022 Rinwasyu
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

layout(std430, binding=0) buffer block_ssbo {
	int block[];
} ssbo;

in vec2 uv;

out vec4 frag_color;

uniform sampler2D texture_sampler;

void main(void) {
	if (ssbo.block[gl_PrimitiveID/12] != 0) {
		frag_color = texture(texture_sampler, uv);
		if (uv.x < 0.01 || uv.x > 0.99 || uv.y < 0.01 || uv.y > 0.99)
			frag_color = vec4(0.3, 1, 0.3, 1);
	} else {
		discard;
	}
}
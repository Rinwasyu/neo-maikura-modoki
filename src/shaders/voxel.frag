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

layout(std430, binding=0) buffer brightness_ssbo {
	float brightness[];
} ssbo;

in vec2 uv;

out vec4 frag_color;

uniform sampler2D texture_sampler;

void main(void) {
	if (ssbo.brightness[gl_PrimitiveID/2] >= 0.0) {
		frag_color = mix(vec4(0,0,0,1), texture(texture_sampler, uv), ssbo.brightness[gl_PrimitiveID/2]);
		if (uv.x < 0.01 || uv.x > 0.99 || uv.y < 0.01 || uv.y > 0.99)
			frag_color = mix(vec4(0, 0, 0, 1), vec4(0.3, 1, 0.3, 1), ssbo.brightness[gl_PrimitiveID/2]);
	} else {
		//if (uv.x < 0.02 || uv.x > 0.98 || uv.y < 0.02 || uv.y > 0.98)
		//	frag_color = vec4(1, 1, 1, 0.1);
		//else
			discard;
	}
}
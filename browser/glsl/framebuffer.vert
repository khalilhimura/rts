#version {VERSION}
{DEFINES}
// SPDX-License-Identifier: GPL-3.0-or-later
uniform vec3 Scroll;
uniform vec3 p1, p2;
in vec3 aVertexPosition;
in vec4 aVertexTexCoord;
in uint aVertexAttributes;
in vec4 aVertexTint;
out vec2 vTexCoord;
out vec4 vTint;
void main()
{
	gl_Position = vec4((aVertexPosition - Scroll) * p1 + p2, 1);
	vTexCoord = aVertexTexCoord.st;
	vTint = aVertexTint;
}

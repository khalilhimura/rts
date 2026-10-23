#version {VERSION}
{DEFINES}
// SPDX-License-Identifier: GPL-3.0-or-later
#ifdef GL_ES
precision mediump float;
#endif
uniform sampler2D Texture0;
uniform bool EnablePixelArtScaling;
in vec2 vTexCoord;
in vec4 vTint;
out vec4 fragColor;
void main()
{
	vec2 coords = vTexCoord;
	if (EnablePixelArtScaling)
	{
		// Same pixel-art filter as combined.frag, without palette/depth paths.
		vec2 size = vec2(textureSize(Texture0, 0));
		vec2 uv = coords * size;
		vec2 offset = fract(uv);
		vec2 pixelsPerTexel = vec2(1.0 / dFdx(uv.x), 1.0 / dFdy(uv.y));
		vec2 interp = clamp(offset * 1.43 * pixelsPerTexel, 0.0, .5) + clamp((offset - 1.0) * 1.43 * pixelsPerTexel + .5, 0.0, .5);
		coords = (floor(coords * size) + interp) / size;
	}
	vec4 color = texture(Texture0, coords);
#ifdef SWAP_TEXTURE_CHANNELS
	color = color.bgra;
#endif
	if (color.a == 0.0)
		discard;
	if (vTint.a < 0.0)
		color = vec4(vTint.rgb, -vTint.a);
	else
		color *= vTint;
	fragColor = color;
}

// SPDX-License-Identifier: GPL-3.0-or-later
namespace OpenRA.Graphics
{
	// Preserve the existing vertex layout for framebuffer-only copies.
	public sealed class FrameBufferShaderBindings : ShaderBindings
	{
		public FrameBufferShaderBindings()
			: base("framebuffer")
		{ }

		public override ShaderVertexAttribute[] Attributes { get; } = new[]
		{
			new ShaderVertexAttribute("aVertexPosition", ShaderVertexAttributeType.Float, 3, 0),
			new ShaderVertexAttribute("aVertexTexCoord", ShaderVertexAttributeType.Float, 4, 12),
			new ShaderVertexAttribute("aVertexAttributes", ShaderVertexAttributeType.UInt, 1, 28),
			new ShaderVertexAttribute("aVertexTint", ShaderVertexAttributeType.Float, 4, 32)
		};
	}
}

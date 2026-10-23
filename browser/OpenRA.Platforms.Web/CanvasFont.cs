// SPDX-License-Identifier: GPL-3.0-or-later
using System;
using System.Runtime.InteropServices.JavaScript;
using System.Runtime.Versioning;
using System.Security.Cryptography;
using Newtonsoft.Json;
using OpenRA.Primitives;

[assembly: SupportedOSPlatform("browser")]

namespace OpenRA.Platforms.Default
{

	// FontFace is loaded from the exact mod font bytes before engine initialization.
	// Bounds use baseline-relative bearings; alpha data has no platform BGRA ambiguity.
	public sealed partial class CanvasFont : IFont
	{
		readonly string family;
		public CanvasFont(byte[] data) => family = "Frontier_" + Convert.ToHexString(SHA256.HashData(data)).ToLowerInvariant();

		[JSImport("glyph", "frontier-fonts")]
		private static partial string Rasterize(string family, string character, int pixels);

		sealed class Glyph
		{
			public int Width { get; set; }
			public int Height { get; set; }
			public int X { get; set; }
			public int Y { get; set; }
			public int Advance { get; set; }
			public string Alpha { get; set; }
		}

		public FontGlyph CreateGlyph(char c, int size, float deviceScale)
		{
			var glyph = JsonConvert.DeserializeObject<Glyph>(Rasterize(family, c.ToString(), (int)(size * deviceScale)));
			return new FontGlyph
			{
				Size = new Size(glyph.Width, glyph.Height),
				Offset = new int2(glyph.X, glyph.Y),
				Advance = glyph.Advance,
				Data = Convert.FromBase64String(glyph.Alpha)
			};
		}

		public void Dispose() { }
	}
}

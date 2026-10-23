// SPDX-License-Identifier: GPL-3.0-or-later
using System.Runtime.InteropServices.JavaScript;

namespace OpenRA.Platforms.Default
{
	// Browser-managed cursors follow input independently of the simulation/render
	// loop. Returning a real handle also prevents CursorManager's software draw.
	sealed partial class WebHardwareCursor : IHardwareCursor
	{
		[JSImport("create", "frontier-cursors")]
		private static partial int Create(byte[] bgra, int width, int height, int x, int y, bool pixelDouble);

		[JSImport("set", "frontier-cursors")]
		private static partial void Set(int id);

		[JSImport("dispose", "frontier-cursors")]
		private static partial void Release(int id);

		readonly int id;

		public WebHardwareCursor(byte[] bgra, int width, int height, int x, int y, bool pixelDouble)
		{
			id = Create(bgra, width, height, x, y, pixelDouble);
		}

		public static void Apply(IHardwareCursor cursor) => Set((cursor as WebHardwareCursor)?.id ?? 0);
		public void Dispose() => Release(id);
	}
}

// SPDX-License-Identifier: GPL-3.0-or-later
using OpenRA.Graphics;
using OpenRA.Traits;

namespace OpenRA.Mods.Frontier
{
	[TraitLocation(SystemActors.World)]
	public sealed class FrontierCameraInfo : TraitInfo<FrontierCamera> { }

	// Center after the HUD has established the viewport dimensions.
	// SDL may not deliver a mouse-motion event until the pointer moves.
	public sealed class FrontierCamera : IPostWorldLoaded
	{
		void IPostWorldLoaded.PostWorldLoaded(World world, WorldRenderer wr)
		{
			if (world.Type == WorldType.Regular && world.LocalPlayer != null && !world.IsLoadingGameSave)
				world.AddFrameEndTask(w =>
				{
					Viewport.LastMousePos = new int2(Game.Renderer.Resolution.Width / 2, Game.Renderer.Resolution.Height / 2);
					wr.Viewport.Center(w.Map.CenterOfCell(w.LocalPlayer.HomeLocation));
				});
		}
	}
}

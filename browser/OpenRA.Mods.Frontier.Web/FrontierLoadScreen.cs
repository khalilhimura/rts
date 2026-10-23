// SPDX-License-Identifier: GPL-3.0-or-later
using OpenRA.Mods.Common.LoadScreens;
using OpenRA.Widgets;

namespace OpenRA.Mods.Frontier
{

	public sealed class FrontierLoadScreen : BlankLoadScreen
	{
		public override void StartGame(Arguments args)
		{
			Ui.ResetAll();
			Game.StartBrowserSkirmish();
		}
	}
}

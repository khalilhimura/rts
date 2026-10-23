// SPDX-License-Identifier: GPL-3.0-or-later
// Original Frontier Collective integration, 2026-10-23.
using System.IO;
using System.Linq;
using OpenRA.Mods.Common.LoadScreens;
using OpenRA.Widgets;

namespace OpenRA.Mods.Frontier
{
	public sealed class FrontierLoadScreen : BlankLoadScreen
	{
		public override void StartGame(Arguments args)
		{
			if (args.GetValue("Launch.Skirmish", "false") != "true")
			{
				base.StartGame(args);
				return;
			}

			var map = Game.ModData.MapCache.Single(m => Path.GetFileName(m.PackageName) == "salt-basin");
			Ui.ResetAll();
			Game.Settings.Save();
			Game.CreateAndStartLocalServer(map.Uid, new[]
			{
				Order.Command("slot_bot Multi1 0 pioneer"),
				Order.Command("option gamespeed default"),
				Order.Command("state Ready")
			});
		}
	}
}

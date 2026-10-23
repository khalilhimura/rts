// SPDX-License-Identifier: GPL-3.0-or-later
using System;
using System.Linq;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;

namespace OpenRA.Mods.Frontier
{
	public sealed class CheckFrontierSprites : IUtilityCommand
	{
		string IUtilityCommand.Name => "--check-frontier-sprites";

		bool IUtilityCommand.ValidateArguments(string[] args) => args.Length == 1;

		[Desc("Decode every sprite frame referenced by the mod, including PNG sheet metadata.")]
		void IUtilityCommand.Run(Utility utility, string[] args)
		{
			Game.ModData = utility.ModData;
			var buildables = utility.ModData.DefaultRules.Actors.Values
				.Where(a => a.TraitInfoOrDefault<BuildableInfo>()?.Queue.Contains("Vehicle") == true).ToArray();
			if (buildables.Length != 4 || buildables.Any(a => a.Name.Contains('.')))
				throw new InvalidOperationException("Expected exactly three combat vehicles and one harvester; preview actors must not be buildable.");
			foreach (var tileset in utility.ModData.DefaultTerrainInfo.Keys)
			{
				using (var sequences = new SequenceSet(utility.ModData.ModFiles, utility.ModData, tileset, null))
					sequences.LoadSprites();
				Console.WriteLine($"PASS: decoded all sequence frames for {tileset}.");
			}
		}
	}
}

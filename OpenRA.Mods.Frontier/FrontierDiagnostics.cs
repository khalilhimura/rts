// SPDX-License-Identifier: GPL-3.0-or-later
// Read-only runtime evidence. Disabled unless FRONTIER_DIAGNOSTICS=1.
using System;
using System.Linq;
using Newtonsoft.Json;
using OpenRA.Mods.Common.Traits;
using OpenRA.Traits;

namespace OpenRA.Mods.Frontier
{
	[TraitLocation(SystemActors.World)]
	public sealed class FrontierDiagnosticsInfo : TraitInfo<FrontierDiagnostics> { }

	public sealed class FrontierDiagnostics : ITick, IGameOver
	{
		readonly bool enabled = Environment.GetEnvironmentVariable("FRONTIER_DIAGNOSTICS") == "1";

		void ITick.Tick(Actor self)
		{
			var world = self.World;
			if (!enabled || world.Type != WorldType.Regular || world.WorldTick % 125 != 0)
				return;

			WriteState(world);
		}

		void IGameOver.GameOver(World world)
		{
			if (enabled)
				WriteState(world);
		}

		static void WriteState(World world)
		{
			Console.WriteLine("FRONTIER_STATE " + JsonConvert.SerializeObject(new
			{
				tick = world.WorldTick,
				players = world.Players.Where(p => p.Playable).Select(p => new
				{
					name = p.InternalName,
					state = p.WinState.ToString(),
					cash = p.PlayerActor.Trait<PlayerResources>().Cash,
					earned = p.PlayerActor.Trait<PlayerResources>().Earned,
					spent = p.PlayerActor.Trait<PlayerResources>().Spent,
					kills = p.PlayerActor.Trait<PlayerStatistics>().UnitsKilled + p.PlayerActor.Trait<PlayerStatistics>().BuildingsKilled,
					actors = world.Actors.Where(a => a.Owner == p && a.Info.HasTraitInfo<HealthInfo>()).Select(a => new
					{
						id = a.ActorID,
						type = a.Info.Name,
						x = a.Location.X,
						y = a.Location.Y,
						hp = a.Trait<Health>().HP
					})
				})
			}));
		}
	}
}

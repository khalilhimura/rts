// SPDX-License-Identifier: GPL-3.0-or-later
using System;
using System.Linq;
using OpenRA.Network;
using OpenRA.Primitives;
using OpenRA.Traits;

namespace OpenRA
{
	public static partial class Game
	{
		public static World BrowserWorld => OrderManager.World;
		public static bool BrowserRestartRequested { get; private set; }
		public static void InitializeBrowser(string[] args)
		{
			BrowserRestartRequested = false;
			Initialize(new Arguments(args));
			ResetBrowserLoop();
		}

		// Normal local lobby settings, using the existing engine's in-memory
		// order connection. Bots submit orders through the local controller.
		public static void StartBrowserSkirmish()
		{
			var map = ModData.MapCache.Single(m => m.Title == "Salt Basin");
			JoinLocal();
			var session = OrderManager.LobbyInfo;
			session.Clients.Clear();
			session.GlobalSettings.Map = map.Uid;
			session.GlobalSettings.RandomSeed = 123456;
			session.GlobalSettings.GameUid = Guid.NewGuid().ToString();
			session.GlobalSettings.EnableSingleplayer = true;

			// Use the same trait-defined defaults as LobbyCommands.LoadMapSettings.
			foreach (var option in map.PlayerActorInfo.TraitInfos<ILobbyOptions>()
				.Concat(map.WorldActorInfo.TraitInfos<ILobbyOptions>()).SelectMany(t => t.LobbyOptions(map)))
				session.GlobalSettings.LobbyOptions[option.Id] = new Session.LobbyOptionState
				{
					Value = option.DefaultValue,
					PreferredValue = option.DefaultValue,
					IsLocked = option.IsLocked
				};

			session.Clients.Add(new Session.Client
			{
				Index = 1,
				Slot = "Multi0",
				Name = "Commander",
				Faction = "collective",
				SpawnPoint = 1,
				State = Session.ClientState.Ready,
				IsAdmin = true,
				Color = Color.FromArgb(255, 240, 140, 50),
				PreferredColor = Color.FromArgb(255, 240, 140, 50)
			});
			session.Clients.Add(new Session.Client
			{
				Index = 2,
				Slot = "Multi1",
				Name = "Pioneer AI",
				Faction = "collective",
				SpawnPoint = 2,
				State = Session.ClientState.Ready,
				Bot = "pioneer",
				BotControllerClientIndex = 1,
				Color = Color.FromArgb(255, 60, 190, 210),
				PreferredColor = Color.FromArgb(255, 60, 190, 210)
			});
			session.Slots["Multi0"] = new Session.Slot { PlayerReference = "Multi0" };
			session.Slots["Multi1"] = new Session.Slot { PlayerReference = "Multi1", AllowBots = true };
			StartGame(map.Uid, WorldType.Regular);
		}
	}
}

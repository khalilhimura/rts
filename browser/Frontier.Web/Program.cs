// SPDX-License-Identifier: GPL-3.0-or-later
using System.Runtime.InteropServices.JavaScript;
using System.Runtime.Versioning;
using Newtonsoft.Json;
using OpenRA;
using OpenRA.Mods.Common.Traits;
using OpenRA.Platforms.Default;
using OpenRA.Widgets;

[assembly: SupportedOSPlatform("browser")]

namespace Frontier.Web
{

	public static partial class Program
	{
		public static void Main() => Console.WriteLine("Frontier browser world host loaded.");

		[JSExport]
		public static void Stage(string path, byte[] bytes)
		{
			if (Path.IsPathRooted(path) || path.Split('/').Contains("..")) throw new ArgumentException("Invalid content path");
			var file = Path.Combine("/openra/engine", path);
			Directory.CreateDirectory(Path.GetDirectoryName(file)!);
			File.WriteAllBytes(file, bytes);
		}

		[JSExport]
		public static string Start()
		{
			try
			{
				WebPlatform.CanvasSize = new OpenRA.Primitives.Size(1280, 800);
				Directory.CreateDirectory("/openra/support");
				Game.InitializeBrowser(new[] { "Engine.EngineDir=/openra/engine", "Engine.SupportDir=/openra/support",
					"Game.Mod=frontier", "Game.Platform=Web", "Graphics.Mode=Windowed", "Graphics.WindowedSize=1280,800",
					"Graphics.GLProfile=Embedded", "Graphics.DisableHardwareCursors=true", "Graphics.VSync=false",
					"Graphics.CapFramerateToGameFps=true" });
				return "OK";
			}
			catch (Exception error) { return error.ToString() + ReadLogs(); }
		}

		static string ReadLogs()
		{
			var path = "/openra/support/Logs";
			return Directory.Exists(path) ? string.Join("\n", Directory.GetFiles(path).Select(f => f + "\n" + File.ReadAllText(f))) : "";
		}

		[JSExport]
		public static bool Step()
		{
			try { Game.BrowserLoopStep(); return Game.BrowserRestartRequested; }
			catch (Exception error) { Console.Error.WriteLine(error.ToString()); throw; }
		}

		[JSExport]
		public static string State()
		{
			var world = Game.BrowserWorld;
			return JsonConvert.SerializeObject(new
			{
				inputModifiers = (int)WebInput.CurrentModifiers,
				menuOpen = Ui.Root.GetOrNull("INGAME_MENU") != null,
				tick = world.WorldTick,
				type = world.Type.ToString(),
				selected = world.Selection.Actors.Select(a => a.ActorID),
				players = world.Players.Where(p => p.Playable).Select(p => new
				{
					name = p.InternalName,
					state = p.WinState.ToString(),
					cash = p.PlayerActor.Trait<PlayerResources>().Cash,
					earned = p.PlayerActor.Trait<PlayerResources>().Earned,
					kills = p.PlayerActor.Trait<PlayerStatistics>().UnitsKilled + p.PlayerActor.Trait<PlayerStatistics>().BuildingsKilled,
					queues = p.PlayerActor.TraitsImplementing<ProductionQueue>().Select(q => new
					{
						type = q.Info.Type,
						items = q.AllQueued().Select(i => new { name = i.Item, ready = i.Done, remaining = i.RemainingTime })
					}),
					actors = world.Actors.Where(a => a.Owner == p && a.Info.HasTraitInfo<HealthInfo>()).Select(a => new
					{
						id = a.ActorID,
						type = a.Info.Name,
						x = a.Location.X,
						y = a.Location.Y,
						hp = a.Trait<Health>().HP
					})
				})
			});
		}

		[JSExport]
		public static void Mouse(int type, int button, int x, int y, int dx, int dy, int modifiers) => WebInput.QueueMouse(type, button, x, y, dx, dy, modifiers);
		[JSExport]
		public static void Key(int type, string code, int modifiers, bool repeat) => WebInput.QueueKey(type, code, modifiers, repeat);
		[JSExport]
		public static void Text(string text) => WebInput.QueueText(text);
	}
}

// SPDX-License-Identifier: GPL-3.0-or-later
// Browser compatibility probe; this does not start a game world.
using System.Diagnostics;
using System.Runtime.InteropServices.JavaScript;
using Newtonsoft.Json;
using OpenRA;
using OpenRA.FileFormats;
using OpenRA.Graphics;
using OpenRA.Mods.Common.Traits;

[assembly: System.Runtime.Versioning.SupportedOSPlatform("browser")]

namespace Frontier.Browser.Probe;

public static partial class Program
{
    public static void Main() => Console.WriteLine("Frontier managed-engine browser probe started; not a playable game.");

    [JSExport]
    public static int RoundTrip(int value) => value;

    [JSExport]
    public static string Inspect(string actorsYaml, string mapYaml, byte[] spriteBytes)
    {
        var clock = Stopwatch.StartNew();
        var types = typeof(Game).Assembly.GetTypes();
        var commonTypes = typeof(BuildableInfo).Assembly.GetTypes();
        var frontierTypes = typeof(OpenRA.Mods.Frontier.FrontierDiagnostics).Assembly.GetTypes();
        var nodes = MiniYaml.FromString(actorsYaml, "frontier/rules/actors.yaml");
        var actors = MiniYaml.Merge(new[] { nodes });
        var required = new[] { "hub", "generator", "refinery", "fabricator", "scout", "tank", "artillery", "harvester" };
        foreach (var name in required)
            if (!actors.Any(a => a.Key == name))
                throw new InvalidDataException("Missing actor: " + name);

        var tank = actors.Single(a => a.Key == "tank");
        var buildable = new BuildableInfo();
        FieldLoader.Load(buildable, tank.Value.Nodes.Single(n => n.Key == "Buildable").Value);
        if (buildable.BuildDuration != 250 || !buildable.Queue.Contains("Vehicle"))
            throw new InvalidDataException("Reflective trait loading differs from desktop rules.");
        var map = MiniYaml.FromString(mapYaml, "salt-basin/map.yaml");
        var title = map.Single(n => n.Key == "Title").Value.Value;
        using var source = new MemoryStream(spriteBytes);
        var png = new Png(source);
        if (png.Type != SpriteFrameType.Rgba32 || png.Width != 512 || png.Height != 64)
            throw new InvalidDataException("Unexpected original eight-direction scout sheet.");

        return JsonConvert.SerializeObject(new
        {
            engineTypes = types.Length, commonTypes = commonTypes.Length, frontierTypes = frontierTypes.Length,
            actors = required, tankBuildDuration = buildable.BuildDuration, map = title,
            width = png.Width, height = png.Height, rgba = Convert.ToBase64String(png.Data),
            managedMs = clock.Elapsed.TotalMilliseconds, runtime = Environment.Version.ToString()
        });
    }

    // Real engine input value type, received through its actual handler interface.
    // The diagnostic sink deliberately has no World, production or combat logic.
    sealed class InputSink : IInputHandler
    {
        public MouseInput Last;
        public void OnMouseInput(MouseInput input) => Last = input;
        public void ModifierKeys(Modifiers mods) { }
        public void OnKeyInput(KeyInput input) { }
        public void OnTextInput(string text) { }
    }

    [JSExport]
    public static string Pointer(int x, int y, int button)
    {
        IInputHandler sink = new InputSink();
        sink.OnMouseInput(new MouseInput(MouseInputEvent.Down, button == 2 ? MouseButton.Right : MouseButton.Left,
            new int2(x, y), int2.Zero, Modifiers.None, 1));
        var input = ((InputSink)sink).Last;
        return JsonConvert.SerializeObject(new { x = input.Location.X, y = input.Location.Y, button = input.Button.ToString() });
    }
}

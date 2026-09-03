using System;
using System.Net.Sockets;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using HarmonyLib;
using UnityEngine;

namespace NuclearTelemetry
{
    [BepInPlugin("com.gameengine.nucleartelemetry", "Nuclear Telemetry & Flight Intelligence", "1.0.0")]
    public class Plugin : BaseUnityPlugin
    {
        internal static ManualLogSource ModLogger;
        private UdpClient _udpClient;
        private const int TargetPort = 8766; // Localhost UDP broadcast
        private float _lastSendTime = 0f;
        private const float UpdateInterval = 0.05f; // 20 Hz update rate

        private void Awake()
        {
            ModLogger = Logger;
            ModLogger.LogInfo("NuclearTelemetry & Flight Intelligence Bridge Initialized.");

            try
            {
                _udpClient = new UdpClient();
                _udpClient.Connect("127.0.0.1", TargetPort);
                ModLogger.LogInfo($"Connected UDP telemetry stream to 127.0.0.1:{TargetPort}");
            }
            catch (Exception ex)
            {
                ModLogger.LogError($"Failed to bind UDP socket: {ex.Message}");
            }

            // Apply Harmony hooks into Nuclear Option game mechanics
            var harmony = new Harmony("com.gameengine.nucleartelemetry");
            harmony.PatchAll();
            ModLogger.LogInfo("Harmony patches injected into Aircraft and CombatHUD systems.");
        }

        private void Update()
        {
            if (Time.time - _lastSendTime < UpdateInterval)
                return;

            _lastSendTime = Time.time;
            SendTelemetry();
        }

        private void SendTelemetry()
        {
            if (_udpClient == null)
                return;

            try
            {
                // Access real Nuclear Option in-game player aircraft via CombatHUD singleton
                Aircraft player = SceneSingleton<CombatHUD>.i != null ? SceneSingleton<CombatHUD>.i.aircraft : null;

                if (player == null || player.disabled)
                    return;

                Vector3 pos = player.transform.position;
                Vector3 vel = player.rb != null ? player.rb.velocity : Vector3.zero;
                float speedMps = vel.magnitude;
                float mach = speedMps / 340.29f; // Sea-level Mach estimation
                float heading = player.transform.eulerAngles.y;
                float fuel = player.fuelLevel;
                bool gear = player.gearDeployed;

                // Format real telemetry payload
                string json = string.Format(
                    "{{\"vehicle\":\"{0}\", \"alt_asl\":{1:F1}, \"alt_agl\":{2:F1}, \"speed_mps\":{3:F1}, \"mach\":{4:F2}, \"heading\":{5:F1}, \"fuel\":{6:F2}, \"gear\":{7}, \"pos\":{{\"x\":{8:F1},\"y\":{9:F1},\"z\":{10:F1}}}}}",
                    player.name,
                    pos.y,
                    pos.y,
                    speedMps,
                    mach,
                    heading,
                    fuel,
                    gear ? "true" : "false",
                    pos.x,
                    pos.y,
                    pos.z
                );

                byte[] bytes = Encoding.UTF8.GetBytes(json);
                _udpClient.Send(bytes, bytes.Length);
            }
            catch (Exception)
            {
                // Transient frame exceptions during scene loading are ignored
            }
        }

        private void OnDestroy()
        {
            _udpClient?.Close();
            _udpClient = null;
        }
    }

    /// <summary>
    /// Harmony Hook: Intercepts missile lock events directed at the player's aircraft.
    /// Demonstrates interaction with in-game Aircraft and Missile classes.
    /// </summary>
    [HarmonyPatch(typeof(Aircraft), nameof(Aircraft.LockedByMissile))]
    public static class Patch_Aircraft_LockedByMissile
    {
        [HarmonyPrefix]
        public static void Prefix(Aircraft __instance, Missile missile)
        {
            if (__instance == null || missile == null)
                return;

            // Check if player aircraft is the one being locked
            if (SceneSingleton<CombatHUD>.i != null && __instance == SceneSingleton<CombatHUD>.i.aircraft)
            {
                Plugin.ModLogger.LogWarning($"[MISSILE WARNING] Inbound threat {missile.name} tracking player!");
            }

        }
    }

    /// <summary>
    /// Harmony Hook: Hooks player missile launch commands.
    /// </summary>
    [HarmonyPatch(typeof(Aircraft), nameof(Aircraft.CmdLaunchMissile))]
    public static class Patch_Aircraft_LaunchMissile
    {
        [HarmonyPrefix]
        public static void Prefix(Aircraft __instance, byte stationIndex, Unit target, GlobalPosition aimpoint)
        {
            if (SceneSingleton<CombatHUD>.i != null && __instance == SceneSingleton<CombatHUD>.i.aircraft)
            {
                string targetName = target != null ? target.name : "Free / GPS Coordinate";
                Plugin.ModLogger.LogInfo($"[FOX AWAY] Player launched ordnance from station {stationIndex} at {targetName}!");
            }
        }
    }
}

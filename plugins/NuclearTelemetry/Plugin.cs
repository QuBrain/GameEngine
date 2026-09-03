using System;
using System.Net.Sockets;
using System.Text;
using BepInEx;
using BepInEx.Logging;
using UnityEngine;

namespace NuclearTelemetry
{
    [BepInPlugin("com.gameengine.nucleartelemetry", "Nuclear Telemetry Bridge", "1.0.0")]
    public class Plugin : BaseUnityPlugin
    {
        private static ManualLogSource _logger;
        private UdpClient _udpClient;
        private const int TargetPort = 8766; // Localhost UDP broadcast
        private float _lastSendTime = 0f;
        private const float UpdateInterval = 0.05f; // 20 Hz update rate

        private void Awake()
        {
            _logger = Logger;
            _logger.LogInfo("NuclearTelemetry Bridge initialized.");

            try
            {
                _udpClient = new UdpClient();
                _udpClient.Connect("127.0.0.1", TargetPort);
                _logger.LogInfo($"Connected UDP stream to 127.0.0.1:{TargetPort}");
            }
            catch (Exception ex)
            {
                _logger.LogError($"Failed to bind UDP socket: {ex.Message}");
            }
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
            if (_udpClient == null) return;

            try
            {
                // In Nuclear Option, the player aircraft can be found via camera or main vehicle tag
                var playerObj = Camera.main != null ? Camera.main.transform : null;
                if (playerObj == null) return;

                Vector3 pos = playerObj.position;
                Vector3 forward = playerObj.forward;

                string json = string.Format(
                    "{{\"alt_asl\":{0:F1}, \"alt_agl\":{1:F1}, \"heading\":{2:F1}, \"pos\":{{\"x\":{3:F1},\"y\":{4:F1},\"z\":{5:F1}}}}}",
                    pos.y,
                    pos.y, // Can be improved with Terrain.activeTerrain.SampleHeight(pos)
                    playerObj.eulerAngles.y,
                    pos.x,
                    pos.y,
                    pos.z
                );

                byte[] bytes = Encoding.UTF8.GetBytes(json);
                _udpClient.Send(bytes, bytes.Length);
            }
            catch (Exception)
            {
                // Ignore transient frame errors
            }
        }

        private void OnDestroy()
        {
            _udpClient?.Close();
        }
    }
}

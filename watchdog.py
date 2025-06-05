# ============== UPDATED ON : 2025-06-03 =================

import json
import time
import subprocess
from datetime import datetime, timedelta
from pytz import timezone
import platform
import os
from logger import logger  

class CameraHealthMonitor:
    def __init__(self, config_path="config.json", status_path="frame_status.json", interval=60, stale_threshold=300):
        self.config_path = config_path
        self.status_path = status_path
        self.check_interval = interval
        self.stale_threshold = stale_threshold
        self.ist = timezone("Asia/Kolkata")
        self.pre_opening_restart_done = False
        self.SERVICE_NAME = "storepulse_demographics_v1.service"
        self.SUDO_PASSWORD = "admin123"
        self.last_service_restarted = None
        self.min_restart_interval = 15 * 60  # 15 minutes in seconds
        self.restart_info_path = "status/restart_info.json"
        self.load_last_restart_time()
        self.load_config()

    def load_last_restart_time(self):
        try:
            if os.path.exists(self.restart_info_path):
                with open(self.restart_info_path, "r") as f:
                    data = json.load(f)
                    last_time_str = data.get("last_service_restarted")
                    if last_time_str:
                        self.last_service_restarted = datetime.strptime(last_time_str, "%Y-%m-%d %H:%M:%S")
                        print(f"[INFO] Loaded last service restart time: {self.last_service_restarted}")
        except Exception as e:
            print(f"[ERROR] Could not load last restart time: {e}")
            
    def save_last_restart_time(self):
        try:
            with open(self.restart_info_path, "w") as f:
                json.dump(
                    {"last_service_restarted": self.last_service_restarted.strftime("%Y-%m-%d %H:%M:%S")},
                    f
                )
        except Exception as e:
            print(f"[ERROR] Could not save last restart time: {e}")


    def load_config(self):
        with open(self.config_path, "r") as f:
            self.config = json.load(f)
        self.cameras = self.config.get("cameras", {})
        self.store_timings = self.config.get("store_timings", {})

    def read_status(self):
        status = {
            "last_frame_produced": {},
            "last_liveframe_uploaded": {}
        }

        try:
            with open("status/last_frame_produced.json", "r") as f:
                status["last_frame_produced"] = json.load(f)
        except Exception as e:
            print(f"[ERROR] Reading last_frame_produced.json: {e}")

        try:
            with open("status/last_liveframe_uploaded.json", "r") as f:
                status["last_liveframe_uploaded"] = json.load(f)
        except Exception as e:
            print(f"[ERROR] Reading last_liveframe_uploaded.json: {e}")

        # Optional: If you want to use last_frame_uploaded.json in future
        try:
            with open("status/last_frame_uploaded.json", "r") as f:
                last_upload = json.load(f).get("LAST_UPLOAD", None)
                print(f"[INFO] Last overall upload: {last_upload}")
        except Exception as e:
            print(f"[ERROR] Reading last_frame_uploaded.json: {e}")

        return status


    def get_camera_ip(self, rtsp_url):
        try:
            return rtsp_url.split("@")[1].split(":")[0]
        except Exception:
            return None
        
    def can_restart_service(self):
        if self.last_service_restarted is None:
            return True
        now = datetime.now(self.ist)
        elapsed = (now - self.last_service_restarted).total_seconds()
        return elapsed >= self.min_restart_interval


    def ping_ip(self, ip):
        param = "-n" if platform.system().lower() == "windows" else "-c"
        count = "1"

        try:
            # Run the ping command and capture output
            completed_process = subprocess.run(
                ["ping", param, count, ip],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            output = completed_process.stdout.lower()

            if platform.system().lower() == "windows":
                # Check for "destination host unreachable" or "request timed out" in output
                if "destination host unreachable" in output or "request timed out" in output:
                    print(f"[WARNING] Camera {ip} is NOT reachable (ICMP unreachable)")
                    return False
                elif "reply from" in output:
                    print(f"[INFO] Camera {ip} is reachable")
                    return True
                else:
                    print(f"[WARNING] Camera {ip} ping response unclear")
                    return False

            else:
                # For Linux/Mac: if returncode is 0, consider reachable
                if completed_process.returncode == 0:
                    print(f"[INFO] Camera {ip} is reachable")
                    return True
                else:
                    print(f"[WARNING] Camera {ip} is NOT reachable")
                    return False

        except Exception as e:
            print(f"[ERROR] Ping failed: {e}")
            return False

        
    # def restart_camera_service(self):
    #     try:
    #         logger.critical("Restarting service due to upload delay.")
    #         subprocess.Popen(
    #             f"sleep 2 && echo {self.SUDO_PASSWORD} | sudo -S systemctl restart {self.SERVICE_NAME}",
    #             shell=True
    #         )
    #     except Exception as e:
    #         logger.error(f"Failed to restart service: {e}")
    
    def restart_camera_service(self):
        if not self.can_restart_service():
            logger.warning("Service restart skipped: too soon since last restart.")
            return
        try:
            logger.critical("Restarting service due to upload delay.")
            subprocess.Popen(
                f"sleep 2 && echo {self.SUDO_PASSWORD} | sudo -S systemctl restart {self.SERVICE_NAME}",
                shell=True
            )
            self.last_service_restarted = datetime.now(self.ist)
            self.save_last_restart_time()
        except Exception as e:
            logger.error(f"Failed to restart service: {e}")

    def is_time_between(self, start_tuple, end_tuple):
        now = datetime.now(self.ist).time()
        start = datetime.strptime(f"{start_tuple[0]}:{start_tuple[1]}", "%H:%M").time()
        end = datetime.strptime(f"{end_tuple[0]}:{end_tuple[1]}", "%H:%M").time()
        return start <= now <= end

    def get_pre_opening_time(self):
        start_hr, start_min = self.store_timings.get("store_start_time", [10, 0])
        opening = datetime.combine(datetime.now(self.ist).date(), datetime.strptime(f"{start_hr}:{start_min}", "%H:%M").time())
        return (opening - timedelta(minutes=5)).time()


    def is_timestamp_stale(self, timestamp_str):
        if not timestamp_str or not isinstance(timestamp_str, str):
            #print("[DEBUG] Timestamp is empty or not a string, considering stale")
            return True
        try:
            # Parse naive datetime from string
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            # Get current IST time but convert it to naive (remove tzinfo)
            now = datetime.now(self.ist).replace(tzinfo=None)
            
            time_diff = (now - timestamp).total_seconds()
            #print(f"[DEBUG] Time difference for timestamp {timestamp_str}: {time_diff} seconds")
            return time_diff > self.stale_threshold
        except ValueError as e:
            print(f"[ERROR] Timestamp format error for '{timestamp_str}': {e}")
            #print("[DEBUG] Considering stale due to format error")
            return True
        except Exception as e:
            print(f"[ERROR] Unexpected error parsing timestamp '{timestamp_str}': {e}")
            #print("[DEBUG] Considering stale due to unexpected error")
            return True


    def monitor_loop(self):
        while True:
            try:
                self.load_config()
                status_data = self.read_status()
                last_frame = status_data.get("last_frame_produced", {})
                last_live = status_data.get("last_liveframe_uploaded", {})

                now = datetime.now(self.ist)
                current_time = now.time()
                pre_opening_time = self.get_pre_opening_time()
                store_close_time = datetime.strptime(f"{self.store_timings['store_close_time'][0]}:{self.store_timings['store_close_time'][1]}", "%H:%M").time()

                # One-time pre-opening restart
                if not self.pre_opening_restart_done and current_time >= pre_opening_time:
                    print(f"[INFO] Pre-opening restart triggered at {now.strftime('%H:%M:%S')}")
                    self.restart_camera_service()
                    self.pre_opening_restart_done = True

                # Main monitoring loop (between pre-opening and close)
                if pre_opening_time <= current_time < store_close_time:
                    print(f"\n[INFO] Checking camera health at {now.strftime('%Y-%m-%d %H:%M:%S')}")
                    for cam_id, rtsp_url in self.cameras.items():
                        frame_time = last_frame.get(cam_id)
                        print(f"frame_time for camera {cam_id}: {frame_time}")
                        live_time = last_live.get(cam_id)
                        print(f"live_time for camera {cam_id}: {live_time}")

                        if self.is_timestamp_stale(frame_time) or self.is_timestamp_stale(live_time):

                            ip = self.get_camera_ip(rtsp_url)
                            if ip:
                                if self.ping_ip(ip):
                                    print(f"[WARNING] Camera {cam_id} is stale but reachable. Restarting service...")
                                    self.restart_camera_service()
                                else:
                                    print(f"[ERROR] CAMERA {cam_id} [{ip}] is OFFLINE")
                            else:
                                print(f"[ERROR] Invalid RTSP for camera {cam_id}")
                else:
                    self.pre_opening_restart_done = False  # Reset flag if outside window

                time.sleep(self.check_interval)
            except Exception as e:
                print(f"[EXCEPTION] {e}")
                time.sleep(self.check_interval)

if __name__ == "__main__":
    monitor = CameraHealthMonitor()
    monitor.monitor_loop()

import time
import sys
import os
from pymavlink import mavutil

# --- COLORS FOR PROFESSIONAL LOOK ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- CONFIGURATION ---
CONNECTION_STRING = 'udp:127.0.0.1:14552'

def clear_screen():
    # Windows ke liye 'cls', Linux/Mac ke liye 'clear'
    os.system('cls' if os.name == 'nt' else 'clear')

def connect_to_sitl():
    print(f"{Colors.BLUE}--- Connecting to SITL on {CONNECTION_STRING} ---{Colors.ENDC}")
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat()
    print(f"{Colors.GREEN}✅ Connected to System {connection.target_system} (Heartbeat Received){Colors.ENDC}")
    return connection

def set_param(connection, param_name, value):
    print(f"{Colors.WARNING}[PARAM] Setting {param_name} to {value}...{Colors.ENDC}")
    connection.mav.param_set_send(
        connection.target_system, connection.target_component,
        param_name.encode('utf-8'), value,
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )
    time.sleep(0.5)

def send_command(connection, command_id, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        command_id, 0,
        p1, p2, p3, p4, p5, p6, p7
    )

def arm_and_takeoff(connection, altitude=20):
    print(f"\n{Colors.BLUE}[ACTION] Switching to GUIDED Mode...{Colors.ENDC}")
    connection.mav.set_mode_send(
        connection.target_system,
        mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED,
        4 
    )
    time.sleep(1)

    print(f"{Colors.BLUE}[ACTION] Arming Motors...{Colors.ENDC}")
    send_command(connection, 400, 1)
    time.sleep(2)
    
    print(f"{Colors.GREEN}[ACTION] Taking Off to {altitude}m... 🚀{Colors.ENDC}")
    send_command(connection, 22, 0, 0, 0, 0, 0, 0, altitude)

def live_monitor(connection):
    print(f"\n{Colors.HEADER}📡 LIVE TELEMETRY MONITOR (Press CTRL+C to Stop){Colors.ENDC}")
    print("-" * 50)
    try:
        while True:
            # GLOBAL_POSITION_INT message ka wait karo
            msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
            if msg:
                # Relative Altitude (mm to meters)
                alt = msg.relative_alt / 1000.0
                # Heading (cdeg to deg)
                hdg = msg.hdg / 100.0
                
                # Dynamic Print (Ek hi line mein update hoga)
                sys.stdout.write(f"\r{Colors.BLUE}>>> Alt: {alt:.2f}m | Hdg: {hdg:.1f}° | Lat: {msg.lat} | Lon: {msg.lon}{Colors.ENDC}")
                sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Stopped Monitoring.{Colors.ENDC}")

def main():
    clear_screen()
    try:
        connection = connect_to_sitl()
    except Exception as e:
        print(f"{Colors.FAIL}Error: {e}{Colors.ENDC}")
        return

    while True:
        print("\n" + "="*50)
        print(f"{Colors.BOLD}{Colors.HEADER} 🚁  CHAOS ENGINEER: ARDUPILOT SITL TOOL (v3.0)  {Colors.ENDC}{Colors.ENDC}")
        print("="*50)
        print(f"1. {Colors.GREEN}🛫  Auto Launch (Arm & Takeoff 20m){Colors.ENDC}")
        print(f"2. {Colors.WARNING}🌪️  Inject High Wind (15 m/s){Colors.ENDC}")
        print(f"3. {Colors.FAIL}🚫  Inject GPS Failure (Glitch){Colors.ENDC}")
        print(f"4. {Colors.BLUE}✅  Reset Conditions (Normal){Colors.ENDC}")
        print(f"5. {Colors.HEADER}📡  Live Telemetry Monitor (New!){Colors.ENDC}")
        print(f"6. 🚪  Exit")
        print("="*50)
        
        choice = input(f"{Colors.BOLD}Select Mission:{Colors.ENDC} ")

        if choice == '1':
            arm_and_takeoff(connection, 20)
        elif choice == '2':
            set_param(connection, 'SIM_WIND_SPD', 15.0)
            set_param(connection, 'SIM_WIND_DIR', 90.0) 
            print(f"{Colors.WARNING}>> High Wind Activated!{Colors.ENDC}")
        elif choice == '3':
            set_param(connection, 'SIM_GPS_DISABLE', 1.0)
            print(f"{Colors.FAIL}>> GPS Disabled! Watch for drift.{Colors.ENDC}")
        elif choice == '4':
            print(f"{Colors.BLUE}>> Resetting parameters...{Colors.ENDC}")
            set_param(connection, 'SIM_WIND_SPD', 0.0)
            set_param(connection, 'SIM_GPS_DISABLE', 0.0)
        elif choice == '5':
            live_monitor(connection)
        elif choice == '6':
            print("Fly safe! Bye.")
            break

if __name__ == "__main__":
    main()

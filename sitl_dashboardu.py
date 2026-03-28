import time
import sys
import os
import csv
from datetime import datetime
from pymavlink import mavutil

# --- COLORS ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    CYAN = '\033[96m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

CONNECTION_STRING = 'udp:127.0.0.1:14552'

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def connect_to_sitl():
    print(f"{Colors.BLUE}--- Connecting to SITL on {CONNECTION_STRING} ---{Colors.ENDC}")
    connection = mavutil.mavlink_connection(CONNECTION_STRING)
    connection.wait_heartbeat()
    print(f"{Colors.GREEN}✅ Connected to System {connection.target_system}{Colors.ENDC}")
    connection.mav.request_data_stream_send(
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_DATA_STREAM_ALL, 4, 1
    )
    return connection

def set_param(connection, param_name, value):
    connection.mav.param_set_send(
        connection.target_system, connection.target_component,
        param_name.encode('utf-8'), value,
        mavutil.mavlink.MAV_PARAM_TYPE_REAL32
    )

def send_command(connection, command_id, p1=0, p2=0, p3=0, p4=0, p5=0, p6=0, p7=0):
    connection.mav.command_long_send(
        connection.target_system, connection.target_component,
        command_id, 0,
        p1, p2, p3, p4, p5, p6, p7
    )

def pre_flight_checks(connection):
    print(f"\n{Colors.HEADER}🔍 RUNNING PRE-FLIGHT DIAGNOSTICS...{Colors.ENDC}")
    msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
    if msg and msg.relative_alt > 1000:
        print(f"[{Colors.FAIL}FAIL{Colors.ENDC}] Drone is ALREADY FLYING!")
        return False
    print(f"{Colors.GREEN}>> ALL SYSTEMS GO. Ready for Launch.{Colors.ENDC}")
    return True

def auto_launch_smart(connection):
    if not pre_flight_checks(connection):
        return
    print(f"\n{Colors.BLUE}[ACTION] Arming & Taking Off...{Colors.ENDC}")
    connection.mav.set_mode_send(connection.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
    send_command(connection, 400, 1)
    time.sleep(1)
    send_command(connection, 22, 0, 0, 0, 0, 0, 0, 20)
    print(f"{Colors.GREEN}>> Launch Sequence Initiated. 🚀{Colors.ENDC}")

# --- NEW FUNCTION: MOVE DRONE ---
def move_drone_manual(connection):
    print(f"\n{Colors.CYAN}🕹️  MANUAL NAVIGATION CONTROL{Colors.ENDC}")
    print("Directions: (N)orth, (S)outh, (E)ast, (W)est, (U)p, (D)own")
    
    direction = input(f"{Colors.BOLD}Enter Direction (N/S/E/W/U/D): {Colors.ENDC}").upper()
    try:
        dist = float(input(f"{Colors.BOLD}Enter Distance in meters (e.g., 5): {Colors.ENDC}"))
    except ValueError:
        print(f"{Colors.FAIL}Invalid distance!{Colors.ENDC}")
        return

    # NED (North East Down) Calculation
    # North = +X, East = +Y, Down = +Z
    x, y, z = 0, 0, 0
    
    if direction == 'N': x = dist
    elif direction == 'S': x = -dist
    elif direction == 'E': y = dist
    elif direction == 'W': y = -dist
    elif direction == 'U': z = -dist # Yaad rakhna: Up means Negative Down
    elif direction == 'D': z = dist
    else:
        print(f"{Colors.FAIL}Invalid Direction!{Colors.ENDC}")
        return

    print(f"{Colors.WARNING}>> Moving Drone {dist}m {direction}...{Colors.ENDC}")
    
    # Send MAVLink Command (SET_POSITION_TARGET_LOCAL_NED)
    # Frame: MAV_FRAME_LOCAL_OFFSET_NED (Target relative to current position)
    connection.mav.set_position_target_local_ned_send(
        0, # time_boot_ms
        connection.target_system, connection.target_component,
        mavutil.mavlink.MAV_FRAME_LOCAL_OFFSET_NED,
        0b110111111000, # Type Mask (Only Position Enabled)
        x, y, z, # Position (x, y, z)
        0, 0, 0, # Velocity
        0, 0, 0, # Accel
        0, 0)    # Yaw

def scenario_death_test(connection):
    print(f"\n{Colors.FAIL}🚨 RUNNING 'DEATH TEST' SCENARIO 🚨{Colors.ENDC}")
    print(f"1. {Colors.GREEN}Auto Takeoff...{Colors.ENDC}")
    connection.mav.set_mode_send(connection.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
    send_command(connection, 400, 1)
    time.sleep(1)
    send_command(connection, 22, 0, 0, 0, 0, 0, 0, 20)
    time.sleep(10)
    print(f"2. {Colors.WARNING}Injecting Wind & GPS Fail...{Colors.ENDC}")
    set_param(connection, 'SIM_WIND_SPD', 20.0)
    set_param(connection, 'SIM_GPS_DISABLE', 1.0)
    print(f"{Colors.BOLD}>> TEST COMPLETE.{Colors.ENDC}")

def main():
    clear_screen()
    try:
        conn = connect_to_sitl()
    except Exception as e:
        print(f"Error: {e}")
        return

    while True:
        print("\n" + "="*60)
        print(f"{Colors.BOLD}{Colors.HEADER} 🚁  CHAOS ENGINEER: NAVIGATOR (v7.0)  {Colors.ENDC}{Colors.ENDC}")
        print("="*60)
        print(f"1. {Colors.GREEN}🛡️   Smart Launch (Safety Checks){Colors.ENDC}")
        print(f"2. {Colors.WARNING}🌪️   Inject High Wind{Colors.ENDC}")
        print(f"3. {Colors.FAIL}🚫   Inject GPS Failure{Colors.ENDC}")
        print(f"4. {Colors.BLUE}✅   Reset Normal{Colors.ENDC}")
        print(f"5. {Colors.FAIL}💀   Run 'Death Test' Scenario{Colors.ENDC}")
        print(f"6. {Colors.CYAN}💾   Blackbox Recorder{Colors.ENDC}")
        print(f"7. {Colors.WARNING}🕹️   Manual Control (Move Drone){Colors.ENDC}")
        print(f"8. Exit")
        
        choice = input(f"\n{Colors.BOLD}Select Mission:{Colors.ENDC} ")

        if choice == '1': auto_launch_smart(conn)
        elif choice == '2': 
            set_param(conn, 'SIM_WIND_SPD', 15.0)
            print(">> Wind Set.")
        elif choice == '3': 
            set_param(conn, 'SIM_GPS_DISABLE', 1.0)
            print(">> GPS Disabled.")
        elif choice == '4':
            set_param(conn, 'SIM_WIND_SPD', 0.0)
            set_param(conn, 'SIM_GPS_DISABLE', 0.0)
            print(">> Reset Done.")
        elif choice == '5': scenario_death_test(conn)
        elif choice == '6': print("Logger feature (Check v5 for code)")
        elif choice == '7': move_drone_manual(conn)
        elif choice == '8': break

if __name__ == "__main__":
    main()

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
    """ Smart Safety Checks before Takeoff """
    print(f"\n{Colors.HEADER}🔍 RUNNING PRE-FLIGHT DIAGNOSTICS...{Colors.ENDC}")
    
    # 1. Check Battery
    sys_status = connection.recv_match(type='SYS_STATUS', blocking=True, timeout=2)
    if sys_status:
        batt_voltage = sys_status.voltage_battery / 1000.0
        if batt_voltage > 10.0:
            print(f"[{Colors.GREEN}PASS{Colors.ENDC}] Battery: {batt_voltage}V")
        else:
            print(f"[{Colors.FAIL}FAIL{Colors.ENDC}] Battery Critical: {batt_voltage}V")
            return False
    
    # 2. Check GPS Lock
    gps_status = connection.recv_match(type='GPS_RAW_INT', blocking=True, timeout=2)
    if gps_status:
        if gps_status.fix_type >= 3: # 3 = 3D Fix
            print(f"[{Colors.GREEN}PASS{Colors.ENDC}] GPS 3D Fix Acquired (Sats: {gps_status.satellites_visible})")
        else:
            print(f"[{Colors.WARNING}WARN{Colors.ENDC}] No GPS Fix (Type: {gps_status.fix_type}). Guided mode might fail.")
    
    # 3. Check if already flying
    msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True, timeout=2)
    if msg and msg.relative_alt > 1000: # > 1 meter
        print(f"[{Colors.FAIL}FAIL{Colors.ENDC}] Drone is ALREADY FLYING (Alt: {msg.relative_alt/1000:.1f}m)!")
        print(f"{Colors.WARNING}>> Aborting Takeoff to prevent crash.{Colors.ENDC}")
        return False

    print(f"{Colors.GREEN}>> ALL SYSTEMS GO. Ready for Launch.{Colors.ENDC}")
    return True

def auto_launch_smart(connection):
    if not pre_flight_checks(connection):
        return # Stop if checks fail
    
    print(f"\n{Colors.BLUE}[ACTION] Arming & Taking Off...{Colors.ENDC}")
    connection.mav.set_mode_send(connection.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
    send_command(connection, 400, 1) # Arm
    time.sleep(1)
    send_command(connection, 22, 0, 0, 0, 0, 0, 0, 20) # Takeoff
    print(f"{Colors.GREEN}>> Launch Sequence Initiated. 🚀{Colors.ENDC}")

def live_logger(connection):
    """ Logs data to CSV file """
    filename = f"flight_log_{datetime.now().strftime('%H%M%S')}.csv"
    print(f"\n{Colors.CYAN}💾 RECORDING BLACKBOX DATA TO: {filename}{Colors.ENDC}")
    print("Press Ctrl+C to Stop Recording...")
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['timestamp', 'altitude_m', 'heading', 'climb_rate']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        try:
            while True:
                msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
                if msg:
                    data = {
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'altitude_m': msg.relative_alt / 1000.0,
                        'heading': msg.hdg / 100.0,
                        'climb_rate': msg.vz / 100.0
                    }
                    writer.writerow(data)
                    sys.stdout.write(f"\rLogging... Alt: {data['altitude_m']:.1f}m")
                    sys.stdout.flush()
        except KeyboardInterrupt:
            print(f"\n{Colors.GREEN}>> Log Saved Successfully.{Colors.ENDC}")

def main():
    clear_screen()
    try:
        conn = connect_to_sitl()
    except:
        return

    while True:
        print("\n" + "="*60)
        print(f"{Colors.BOLD}{Colors.HEADER} 🚁  CHAOS ENGINEER: SMART PILOT (v5.0)  {Colors.ENDC}{Colors.ENDC}")
        print("="*60)
        print(f"1. {Colors.GREEN}🛡️   Smart Launch (Safety Checks + Takeoff){Colors.ENDC}")
        print(f"2. {Colors.WARNING}🌪️   Wind Injection (15 m/s){Colors.ENDC}")
        print(f"3. {Colors.FAIL}🚫   GPS Failure (Glitch){Colors.ENDC}")
        print(f"4. {Colors.CYAN}📊   Live Visual Dashboard{Colors.ENDC}")
        print(f"5. {Colors.BLUE}💾   Blackbox Recorder (Save CSV){Colors.ENDC}")
        print(f"6. {Colors.FAIL}💀   Run 'Death Test' Scenario{Colors.ENDC}")
        print(f"7. Exit")
        
        choice = input(f"\n{Colors.BOLD}Select Mission:{Colors.ENDC} ")

        if choice == '1':
            auto_launch_smart(conn)
        elif choice == '2':
            set_param(conn, 'SIM_WIND_SPD', 15.0)
            set_param(conn, 'SIM_WIND_DIR', 90.0) 
            print(f"{Colors.WARNING}>> High Wind Activated!{Colors.ENDC}")
        elif choice == '3':
            set_param(conn, 'SIM_GPS_DISABLE', 1.0)
            print(f"{Colors.FAIL}>> GPS Disabled!{Colors.ENDC}")
        elif choice == '4':
            # (Dashboard code same as before - omitted for brevity, add previous logic here if needed)
            print("Dashboard selected (Use previous code)") 
        elif choice == '5':
            live_logger(conn)
        elif choice == '7':
            break

if __name__ == "__main__":
    main()

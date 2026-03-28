import time
import sys
import os
from pymavlink import mavutil

# --- COLORS & STYLING ---
class Colors:
    HEADER = '\033[95m'  # Pink/Purple
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m' # Yellow
    FAIL = '\033[91m'    # Red
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

def draw_bar(label, value, max_val, color):
    """ Terminal mein graphic bar banane ka function """
    bar_len = 30 # Bar ki lambai
    clamped_val = max(0, min(value, max_val)) # Value limit mein rakho
    fill_len = int((clamped_val / max_val) * bar_len)
    
    bar = '█' * fill_len + '░' * (bar_len - fill_len)
    return f"{color}{label:<10} |{bar}| {value:6.2f}{Colors.ENDC}"

def live_dashboard(connection):
    print(f"\n{Colors.HEADER}📡  LIVE FLIGHT DATA VISUALIZER (Ctrl+C to Stop)  📡{Colors.ENDC}")
    try:
        while True:
            # Data maango
            msg = connection.recv_match(type='GLOBAL_POSITION_INT', blocking=True)
            if msg:
                # Calculations
                alt = msg.relative_alt / 1000.0  # mm to meters
                speed = (msg.vx**2 + msg.vy**2)**0.5 / 100.0 # Speed m/s
                
                # Screen ko 'Rewrite' karo (Animation effect ke liye)
                sys.stdout.write("\033[K") # Clear line
                # 3 Bars Print karo
                print(f"\r{Colors.BOLD}STATUS MONITOR:{Colors.ENDC}")
                print(draw_bar("Altitude", alt, 50.0, Colors.CYAN) + " m")
                print(draw_bar("Speed", speed, 20.0, Colors.WARNING) + " m/s")
                print(draw_bar("Heading", msg.hdg/100.0, 360.0, Colors.GREEN) + " deg")
                
                # Cursor ko wapas upar bhejo taaki wahi overwrite ho
                sys.stdout.write("\033[4A") 
                sys.stdout.flush()
                
    except KeyboardInterrupt:
        # Cursor fix karo exit par
        sys.stdout.write("\033[4B")
        print(f"\n{Colors.FAIL}Monitor Stopped.{Colors.ENDC}")

def scenario_death_test(connection):
    """ Automated Test Sequence """
    print(f"\n{Colors.FAIL}🚨 RUNNING 'DEATH TEST' SCENARIO 🚨{Colors.ENDC}")
    
    print(f"1. {Colors.GREEN}Auto Takeoff...{Colors.ENDC}")
    connection.mav.set_mode_send(connection.target_system, mavutil.mavlink.MAV_MODE_FLAG_CUSTOM_MODE_ENABLED, 4)
    send_command(connection, 400, 1) # Arm
    time.sleep(1)
    send_command(connection, 22, 0, 0, 0, 0, 0, 0, 20) # Takeoff 20m
    
    for i in range(10, 0, -1):
        sys.stdout.write(f"\rWait for Altitude... {i}s ")
        sys.stdout.flush()
        time.sleep(1)
    print(" -> OK")

    print(f"2. {Colors.WARNING}Injecting 20m/s WIND...{Colors.ENDC}")
    set_param(connection, 'SIM_WIND_SPD', 20.0)
    time.sleep(3)

    print(f"3. {Colors.FAIL}KILLING GPS NOW! (Good luck)...{Colors.ENDC}")
    set_param(connection, 'SIM_GPS_DISABLE', 1.0)
    
    print(f"\n{Colors.BOLD}>> TEST COMPLETE. Check Map for crash/drift! <<{Colors.ENDC}")
    time.sleep(2)

def main():
    clear_screen()
    try:
        conn = connect_to_sitl()
    except:
        print("SITL not found.")
        return

    while True:
        print("\n" + "="*50)
        print(f"{Colors.BOLD}{Colors.HEADER} 🚁  CHAOS ENGINEER PRO (v4.0)  {Colors.ENDC}{Colors.ENDC}")
        print("="*50)
        print(f"1. {Colors.GREEN}🛫  Auto Launch (20m){Colors.ENDC}")
        print(f"2. {Colors.WARNING}🌪️  Wind Injection (15 m/s){Colors.ENDC}")
        print(f"3. {Colors.FAIL}🚫  GPS Failure (Glitch){Colors.ENDC}")
        print(f"4. {Colors.CYAN}📊  Live Visual Dashboard (GRAPHICS){Colors.ENDC}")
        print(f"5. {Colors.FAIL}💀  Run 'Death Test' Scenario (Auto){Colors.ENDC}")
        print(f"6. {Colors.BLUE}✅  Reset Normal{Colors.ENDC}")
        print(f"7. Exit")
        
        choice = input(f"\n{Colors.BOLD}Select Mission:{Colors.ENDC} ")

        if choice == '1':
            send_command(conn, 22, 0, 0, 0, 0, 0, 0, 20)
        elif choice == '4':
            live_dashboard(conn)
        elif choice == '5':
            scenario_death_test(conn)
        elif choice == '6':
            set_param(conn, 'SIM_WIND_SPD', 0)
            set_param(conn, 'SIM_GPS_DISABLE', 0)
        elif choice == '7':
            break

if __name__ == "__main__":
    main()

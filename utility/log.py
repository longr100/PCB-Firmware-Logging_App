import argparse
import serial
import struct
import os

parser = argparse.ArgumentParser(
	description=__doc__,
	formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('action', 
	action='store', 
	choices=['log-dump', 'log-clear', 'log-test'],
	help='Action to perform')

parser.add_argument('-p', 
	action='store',
	dest='port',
	help='COM port to use')

args, remaining = parser.parse_known_args()
LOG_TYPES = ["RESET", "WAKE", "PUMP", "CLOCK ERROR"]
RESET_REASONS = {0x1 : "POWER ON", 0x2 : "BROWN OUT", 0x4 : "EXTERNAL", 0x8 : "WDT", 0x10 : "SOFTWARE", 0x20 : "UPDI"}
WAKE_REASONS = ["UNDEFINED", "POWER ON", "RTC", "OK BTN", "USB"]
PUMP_REASONS = ["AUTO", "MANUAL"]

def auto_port():
	from serial.tools import list_ports
	ports = list_ports.comports()
	port = None

	if not ports:
		raise Exception("No COM ports found.")
	
	for p in ports:
		if "VID:PID=0403:6015" in p.hwid:
			port = p.device
			print(f"Using port: {port}")
			break
			
	if (not port):
		print("Unable to detect COM port")
		port = select_port()
		
	return port

def select_port():
	from serial.tools import list_ports
	ports = list_ports.comports()

	if not ports:
		raise Exception("No COM ports found.")

	print("Available COM ports:")
	for i, port in enumerate(ports, start=1):
		print(f"{i}: {port.device} - {port.manufacturer} - {port.description}")
		
	print("\nEnter the number of the port you want to select:")
	selected_port = int(input())

	if selected_port < 1 or selected_port > len(ports):
		raise Exception("Invalid selection.")

	port = ports[selected_port-1]

	print(f"\nSelected Port: {port.device}")
	print ("Device details:")
	print(f"    Desc: {port.description}")
	print(f"    Mfg: {port.manufacturer}")
	print(f"    HWID: {port.hwid}\n")
	
	return port.device
	
def dump_log():
	port = args.port
	
	if (port == "auto"):
		port = auto_port();
	elif (not port):
		port = select_port();
		
	s = serial.Serial(port, 9600, timeout=5, write_timeout=5)
	s.write(b"D\n")
	s.read_until()
	s.read_until()
	dev_id = s.read_until().decode('utf-8').strip()
	data = s.read_until(b"\nLOG DUMP END\n")
	
	s.close()
	
	data = data[:-14]
	#print_buffer(data)
	
	os.makedirs("logs", exist_ok=True)
	
	logf = open("./logs/" + dev_id + ".csv", 'a+')
	
	print(f"Device ID: {dev_id}\n")
	print(f"{'ID':<6}{'TYPE':<12}{'DATE':<9}{'TIME':<6}{'REASON':<10}{'CHIP TEMP C':<12}{'PCB TEMP C':<12}{'VOLTS':<6}")
	
	if (logf.tell() == 0):
		logf.write("ID,TYPE,DATE,TIME,REASON,CHIP TEMP C,PCB TEMP C,VOLTS\n")
	
	i = 0
	while (i < len(data)):
		hdr = struct.unpack_from("<BH5B", data, offset=i)
		
		date = f"{hdr[2]:0>2}-{hdr[3]:0>2}-{hdr[4]:0>2}"
		time = f"{hdr[5]:0>2}:{hdr[6]:0>2}"
		
		csv_line = f"{hdr[1]},{LOG_TYPES[hdr[0]]},{date},{time}"
		print_line = f"{hdr[1]:<6}{LOG_TYPES[hdr[0]]:<12}{date:<9}{time:<6}"
		
		i+=8
		
		match hdr[0]:
			case 0|2: #RESET | PUMP
				body = struct.unpack_from("<BhhH", data, offset=i)
				reason = None
				
				if (hdr[0] == 0):
					reason = RESET_REASONS.get(body[0], '')
				else:
					reason = PUMP_REASONS[body[0]]
				
				temp_chip = body[1] / 10
				temp_pcb = body[2] / 10
				volts = body[3] / 100
				
				csv_line += f",{reason},{temp_chip},{temp_pcb},{volts}\n"
				print_line += f"{reason:<10}{temp_chip:<12}{temp_pcb:<12}{volts:<6}"
				i+=7
				
			case 1: #WAKE
				body = struct.unpack_from("B", data, offset=i)
				csv_line += f",{WAKE_REASONS[body[0]]},,,\n"
				print_line += f"{WAKE_REASONS[body[0]]:<10}"
				i+=1
				
			case 3: #OSC_ERR
				csv_line += ",,,,\n"
		
		print(print_line)
		logf.write(csv_line)
		
	logf.close()
	
	
def clear_log():
	port = args.port
	
	if (port == "auto"):
		port = auto_port();
	elif (not port):
		port = select_port();
		
	print("Erasing log, please wait...")
		
	s = serial.Serial(port, 9600, timeout=5, write_timeout=5)
	s.write(b"C\n")
	s.read_until()
	s.read_until()
	
	s.close()
	
	print("Done")
	
def test_log():
	port = args.port
	
	if (port == "auto"):
		port = auto_port();
	elif (not port):
		port = select_port();
		
	print("Log memory test in progress, please wait...")
		
	s = serial.Serial(port, 9600, timeout=5, write_timeout=5)
	s.write(b"T\n")
	s.read_until()
	s.read_until()
	data = s.read_until(b"\nLOG TEST END\n")
	data = data[:-14]
	
	print_buffer(data)
	
	s.close()
	
def print_buffer(data):
	addr = 0
	print(f"{len(data)} bytes")
	for i, d in enumerate(data):
		if (i % 16 == 0):
			print(f"{addr:04X}:", end=' ')
			addr += 16
		
		print(f"{d:02X}", end=' ')
		if ((i +1) % 16 == 0):
			print()
		if ((i +1) % 32 == 0):
			print()
	print()
	
try:
	print("WPZ Scent Dispenser Log Download Script\n")
	
	match args.action:
		case 'log-dump':
			dump_log()
			
		case 'log-clear':
			clear_log()
			
		case 'log-test':
			test_log()
			
		case _:
			print('Unknown option')

except Exception as e:
	parser.exit(type(e).__name__ + ': ' + str(e))
import argparse
import serial
import logging

logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARNING)

parser = argparse.ArgumentParser(
	description=__doc__,
	formatter_class=argparse.RawDescriptionHelpFormatter)

parser.add_argument('action', 
	action='store', 
	choices=['flash', 'set-id'],
	help='Action to perform')

parser.add_argument('-f', 
	action='store', 
	dest='file',
	help='Hex file to flash',
	nargs='?')

parser.add_argument('-p', 
	action='store',
	dest='port',
	help='COM port to use')

parser.add_argument('-n',
	action='store',
	dest='dev_id',
	help='Device ID to assign',
	nargs='?')

args, remaining = parser.parse_known_args()
pymcu = None

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
	
def init_mcuprog(erase):
	global pymcu
	
	port = args.port
	if (not port):
		port = select_port();
		
	print("Connecting to device, please wait...");
		
	from pymcuprog.backend import SessionConfig
	sessionconfig = SessionConfig("attiny1617")
	
	sessionconfig.special_options = {}
	
	if (erase == True):
		sessionconfig.special_options["chip-erase-locked-device"] = True
	else:
		sessionconfig.special_options["user-row-locked-device"] = True

	from pymcuprog.toolconnection import ToolSerialConnection
	transport = ToolSerialConnection(serialport=port, timeout=5)

	from pymcuprog.backend import Backend
	pymcu = Backend()

	pymcu.connect_to_tool(transport)
	pymcu.start_session(sessionconfig)
	
	print("Connected");
	
def close_mcuprog():
	pymcu.end_session()
	pymcu.disconnect_from_tool()
	
	print("Disconnected");

def ping():
	device_type = pymcu.read_device_id()
	print ("Device Type is {0:06X}".format(int.from_bytes(device_type, byteorder="little")))
	
def get_id():
	mem = pymcu.read_memory(memory_name='user_row', numbytes=16)
	data = mem[0].data
	dev_id = data.decode('utf-8').strip('\x00')
	print(f"Device ID: {dev_id}")
	
def set_id(dev_id):
	if (len(dev_id) > 16): return
	data = dev_id.strip().encode('utf-8').ljust(16, b'\0')
	data = data[0:16]
	
	mem = pymcu.write_memory(data, memory_name='user_row')
	print(f"New Device ID: {dev_id}")
	
def flash(file):
	print("Erasing device, please wait...")
	pymcu.erase()
	print("Flashing firmware, please wait...")
	pymcu.write_hex_to_target(file)
	print("Done")
	
try:
	print("WPZ Scent Dispenser Firmware Flash Script\n")
	
	match args.action:
		case 'set-id':
			if (not args.dev_id):
				print("No device id specified")
			else:
				init_mcuprog(False)
				set_id(args.dev_id)
				close_mcuprog()
				
		case 'flash':
			if (not args.file):
				print("No hex file specified")
			else:
				init_mcuprog(True)
				flash(args.file)
				close_mcuprog()
			
		case _:
			print('Unknown option')

except Exception as e:
	parser.exit(type(e).__name__ + ': ' + str(e))
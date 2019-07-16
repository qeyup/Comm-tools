#!/usr/bin/python3


# Required modules
import argparse
import os
import sys
import serial
import pty
import subprocess
import time
import importlib
import imp
import traceback
import socket
import sys
import threading


# Set version
script_version="0.1.1"


# Template
class SimuationTemplate:
    # Constructor
    def __init__(self, args):
        return

    # Destructor
    def __del__(self):
        return
    
    # Send data
    def sendData(self, bytes_fame):
        return

    # Read data
    def readData(self):
        return b''


# Serial port simulation
class serialSimulation:

    # Constructor
    def __init__(self, args):
        print("+ Started serial device simulation")

        # Generate device name
        if not os.path.exists(args.device_path):
            os.makedirs(args.device_path)
        device_port = '%s/tty_%s' % (args.device_path, args.name)
        Internal_port = '%s/.tty_%s'  % (args.device_path, args.name)
        i=1
        while os.path.islink(device_port):
            if not os.path.exists(os.readlink(device_port)):
                os.remove(device_port)
                break
            device_port = '%s/tty_%s_%i' % (args.device_path, args.name, i)
            Internal_port = '%s/.tty_%s_%i'  % (args.device_path, args.name, i)
            i += 1


        # Generate virtual port
        cmd= ['/usr/bin/socat','-d','-d','pty,raw,echo=0,link=%s' % device_port, 'pty,raw,echo=0,link=%s' % Internal_port]
        self.proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        time.sleep(1)
        print ("- Created device: %s" % device_port)

        self.ser = serial.Serial(Internal_port, args.serial_baud, rtscts=True,dsrdtr=True, timeout=0)
        err = ''
        out = ''
        return

    # Destructor
    def __del__(self):
        print("+ Terminated serial device simulation")
        if self.proc != None:
            self.proc.terminate()
        return

    # Send data
    def sendData(self, bytes_fame):
        self.ser.write(bytes_fame)
        return

    # Read data
    def readData(self):
        return self.ser.read()


# TCP-Listener
class tcpListenSimulation:
    # Constructor
    def __init__(self, args):
        print("+ Started serial device simulation")
        # Create listen socket
        HOST = '' # Symbolic name, meaning all available interfaces
        PORT = int(args.listen_port) # Arbitrary non-privileged port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        print ('- Socket created listening at port %s' % PORT)


        try:
            # Bind socket to local host and port
            self.s.bind((HOST, PORT))
            print ('- Socket bind complete')
        except socket.error as msg:
            print ('Bind failed!')


        #Start listening on socket
        self.s.listen(1)
        print ('- Socket now listening')


        # wait for connection
        self.conn, addr = self.s.accept()
        print ('- Connected with ' + addr[0] + ':' + str(addr[1]))
        return

    # Destructor
    def __del__(self):
        self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()
        return
    
    # Send data
    def sendData(self, bytes_fame):
        try:
            self.conn.sendall(bytes_fame)
        except:
            print ("- Connection lost (TX)")
        return

    # Read data
    def readData(self):
        try:
            data = self.conn.recv(1024)
        except:
            print ("- Connection lost (RX)")

        if not data:
            print ("- Need reconnection")
            self.conn, addr = self.s.accept()
            print ('- Connected with ' + addr[0] + ':' + str(addr[1]))
        return data


# Main function
def main(argv=sys.argv[1:]):

    # Parse args
    parser = argparse.ArgumentParser(
        description='Tool used to simulate communication endpoint and automatic responses for testing purposes',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--type',
        required=False,
        default="serial",
        choices=["serial", "tcp-listen"],
        help='Conextion type')
    parser.add_argument(
        '--name',
        required=False,
        default="",
        help='name')
    parser.add_argument(
        '--device-path',
        required=False,
        default=".",
        help='path where the device will be created')
    parser.add_argument(
        '--module-path',
        required=False,
        default=".",
        help='path where the response script will be created/read')
    parser.add_argument(
        '--serial-baud',
        required=False,
        default=9600,
        help='Serial port baud. (only for --type serial)')
    parser.add_argument(
        '--listen-port',
        required=False,
        default=5000,
        help='Listener port.  (only for --type tcp-listen)')
    parser.add_argument(
        '--print-input-raw',
        required=False,
        default=False,
        action='store_true',
        help='Print input (in bytes)')
    parser.add_argument(
        '--print-input-ascii',
        required=False,
        default=False,
        action='store_true',
        help='Print input (in ascii)')
    parser.add_argument(
        '--print-input-processed-raw',
        required=False,
        default=False,
        action='store_true',
        help='Print processed input only when the input is processed (in bytes)')
    parser.add_argument(
        '--print-input-processed-ascii',
        required=False,
        default=False,
        action='store_true',
        help='Print processed input only when the input is processed (in ascii)')
    parser.add_argument(
        '--print-output-raw',
        required=False,
        default=False,
        action='store_true',
        help='Print output (in bytes)')
    parser.add_argument(
        '--print-output-ascii',
        required=False,
        default=False,
        action='store_true',
        help='Print output (in ascii)')
    args = parser.parse_args(argv)


    # Process args
    if args.name == "":
        args.name = args.type


    # execute connection type
    try:
        print('\nstarting..')
        print ("- Conexion type: %s" % args.type)


        # Create simulation object
        if args.type == "serial":
            sim = serialSimulation(args)
        elif args.type == "tcp-listen":
            sim = tcpListenSimulation(args)


        # Check simulation device
        if (sim == None):
            print ("Simulation error")
            return


        # Generate/read response script and read static data
        def procesResponseFile():
            module_name =  "%s_response_module" % (args.name)
            module_path = os.path.join(args.module_path, module_name)
            if not os.path.exists(module_path):
                os.makedirs(module_path)
            print ("- Response module: %s" % module_path)
            scritp_file = os.path.join(module_path, "__init__.py")

            if os.path.isfile(scritp_file):
                print ("- Response module exists")
            else:
                file_content = ""
                file_content += "# Static data.\n"
                file_content += "# Note: is necesary to restart execution to apply any change in the static data\n"
                file_content += "class static_data:\n"
                file_content += "   # Trigger/timeout time (in seconds). set to None to wait for data.\n"
                file_content += "   module_timeout = 1\n"
                file_content += "\n"
                file_content += "   # Aux\n"
                file_content += "   Obj = None\n"
                file_content += "   Counter = [0]\n"
                file_content += "   Bool = [False]\n"
                file_content += "   String = ['']\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "# Process incoming data and send response.\n"
                file_content += "# Note: Is NOT necesary to restart execution to apply any change in processData() function.\n"
                file_content += "def processData(static, input_bytes, output_bytes):\n"
                file_content += "   input_bytes = b''\n"
                file_content += "   output_bytes = b''\n"
                file_content += "   return static, input_bytes, output_bytes\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "# Send data each time module timeout is trigger.\n"
                file_content += "# Note: Is NOT necesary to restart execution to apply any change in sendData() function.\n"
                file_content += "def sendData(static):\n"
                file_content += "   output_bytes=b''\n"
                file_content += "   return static, output_bytes\n"
                file_content += "\n"
                file = open(scritp_file, "w") 
                file.write(file_content)
                file.close()

                print ("- Response module created")

            # Import module
            sys.path.append(args.module_path)
            try:
                module = __import__(module_name)
            except Exception as e:
                print ("error: '%s' -> %s" % (scritp_file, e))
                return None

            return module
        module = procesResponseFile()
        if module == None:
            return


        # define run boolean
        run = True


        # Define reader thread
        def reader():
            print ("-", threading.currentThread().getName(), 'Lanzado')

            # Initialize variables
            last_error=""
            frame=b""
            shared = module.static_data()

            # Read from device
            while run:
                try:
                    # Reload module (to get changes)
                    imp.reload(module)

                    # Read data
                    byte = sim.readData()

                    # Process data
                    if byte != b"":
                        if args.print_input_raw == True :
                            print("> input (hex): %s" % bytes(byte).hex())
                        if args.print_input_ascii == True:
                            try:
                                print("> input (ascii): %s" % bytes(byte).decode('ascii'))
                            except Exception as e:
                                print (e)
                        frame += bytes(byte)
                        frame_aux = frame
                        response = b""
                        shared, frame,response = module.processData(shared, frame, response)
                        if last_error != "":
                            last_error = ""
                            print("Module error is fix now.")
                        if frame != frame_aux:
                            if args.print_input_processed_raw == True :
                                print("> input* (hex): %s" % bytes(frame_aux).hex())
                            if args.print_input_processed_ascii == True:
                                try:
                                    print("> input* (ascii): %s" % bytes(frame_aux).decode('ascii'))
                                except Exception as e:
                                    print (e)
                        if response != b"":
                            if args.print_output_raw == True :
                                print("< output (hex): %s" % bytes(response).hex())
                            if args.print_output_ascii == True:
                                try:
                                    print("< output (ascii): %s" % bytes(response).decode('ascii'))
                                except Exception as e:
                                    print (e)
                            sim.sendData(response)
                except Exception as e:
                    frame=b''
                    if (run == True) and (last_error != traceback.format_exc()):
                        last_error = traceback.format_exc()
                        print(traceback.format_exc())
            print ("-", threading.currentThread().getName(), 'Deteniendo')


        # Define sender thread
        def sender():
            print ("-", threading.currentThread().getName(), 'Lanzado')
            # Initialize variables
            last_error=""
            shared = module.static_data()

            while run:
                try:
                    # Reload module (to get changes)
                    imp.reload(module)

                    # Wait
                    time.sleep(shared.module_timeout)

                    # send data
                    shared, output_frame = module.sendData(shared)
                    if last_error != "":
                        last_error = ""
                        print("Module error is fix now.")
                    if output_frame != b"":
                        if args.print_output_raw == True :
                            print("< output (hex): %s" % bytes(output_frame).hex())
                        if args.print_output_ascii == True:
                            try:
                                print("< output (ascii): %s" % bytes(output_frame).decode('ascii'))
                            except Exception as e:
                                print (e)
                        sim.sendData(output_frame)
                except Exception as e:
                    if (run == True) and (last_error != traceback.format_exc()):
                        last_error = traceback.format_exc()
                        print(traceback.format_exc())
            print ("-", threading.currentThread().getName(), 'Deteniendo')


        # Create threads
        reader_thread = threading.Thread(target=reader, name='Simulator Reader')
        sender_thread = threading.Thread(target=sender, name='Simulator Sender')


        # start threads
        reader_thread.start()
        sender_thread.start()


        # Wait for threads
        reader_thread.join()
        sender_thread.join()

    except KeyboardInterrupt:
        print("\n")
        pass

    finally:
        print ("- Wait to threads to terminate")
        run = False
        reader_thread.join()
        sender_thread.join()


# Main execution
if __name__ == '__main__':
    sys.exit(main())

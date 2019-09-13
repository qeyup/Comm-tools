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
#import imp
import traceback
import socket
import sys
import threading
import hashlib


# Set version
script_version="0.2.2"

# log
def log(log, log_type =""):
    for log_string in log.split("\n"):
        if log_string == "":
            print("\n")
        elif log_type == "warning":
            print("! %s" % log_string)
        elif log_type == "error":
            print("# %s" % log_string)
        elif log_type == "info":
            print("+ %s" % log_string)
        elif log_type == "tx":
            print("< %s" % log_string)
        elif log_type == "rx":
            print("> %s" % log_string)
        else:
            print("- %s" % log_string)


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
        log("+ Started serial device simulation")

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
        log("Created device: %s" % device_port)

        self.ser = serial.Serial(Internal_port, args.serial_baud, rtscts=True,dsrdtr=True, timeout=0)
        err = ''
        out = ''
        return

    # Destructor
    def __del__(self):
        log("Terminated serial device simulation", "info")
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
        log("Started serial device simulation", "info")
        # Create listen socket
        HOST = '' # Symbolic name, meaning all available interfaces
        PORT = int(args.listen_port) # Arbitrary non-privileged port
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        log('Socket created listening at port %s' % PORT)


        retry = True
        while retry:
            last_error = ""
            try:
                # Bind socket to local host and port
                #time.sleep(2)
                self.s.bind((HOST, PORT))
                log('Socket bind complete')
                retry = False
            except socket.error as msg:
                if last_error != msg:
                    #print (msg)
                    last_error = msg


        #Start listening on socket
        self.s.listen(1)
        log('Socket now listening')


        # wait for connection
        self.conn, addr = self.s.accept()
        log('Connected with ' + addr[0] + ':' + str(addr[1]))
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
            log("Connection lost (TX)", "warning")
        return

    # Read data
    def readData(self):
        try:
            data = self.conn.recv(1024)
        except:
            log("Connection lost (RX)", "warning")

        if not data:
            log("Need reconnection", "waring")
            self.conn, addr = self.s.accept()
            log('Connected with ' + addr[0] + ':' + str(addr[1]), "info")
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
        '--id',
        required=False,
        default="",
        help='ID passed to the module. If is not given, an empty string will be save.')
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
        log('\nstarting..')
        log ("Conexion type: %s" % args.type)


        # Create simulation object
        if args.type == "serial":
            sim = serialSimulation(args)
        elif args.type == "tcp-listen":
            sim = tcpListenSimulation(args)


        # Check simulation device
        if (sim == None):
            log("Simulation error", "error")
            return


        # Get last change date method
        def getModuleHash():
            module_name =  "%s_response_module" % (args.name)
            module_path = os.path.join(args.module_path, module_name)
            init_path = os.path.join(module_path, "__init__.py")
            return hashlib.md5(open(init_path,'rb').read()).hexdigest()


        # Get last change date method
        def getModuleLastUpdate():
            module_name =  "%s_response_module" % (args.name)
            module_path = os.path.join(args.module_path, module_name)
            init_path = os.path.join(module_path, "__init__.py")
            return time.ctime(os.path.getmtime(init_path))


        # Generate/read response script and read static data
        def procesResponseFile():
            module_name =  "%s_response_module" % (args.name)
            module_path = os.path.join(args.module_path, module_name)
            if not os.path.exists(module_path):
                os.makedirs(module_path)
            log("Response module: %s" % module_path)
            scritp_file = os.path.join(module_path, "__init__.py")

            if os.path.isfile(scritp_file):
                log("Response module exists")
            else:
                file_content =  "# CommTool simulated device module.\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "# Initialize static data map.\n"
                file_content += "def initStaticData():\n"
                file_content += "    static = {}\n"
                file_content += "    return static\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "# Reload static data map. This method is only called when the file is modify during the run time.\n"
                file_content += "def reloadStaticData(static):\n"
                file_content += "    return static\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "# Process incoming data and send response\n"
                file_content += "def processData(static, input_bytes, output_bytes):\n"
                file_content += "    input_bytes = b''\n"
                file_content += "    output_bytes = b''\n"
                file_content += "    return static, input_bytes, output_bytes\n"
                file_content += "\n"
                file_content += "\n"
                file_content += "# Send data each time module timeout is trigger\n"
                file_content += "def sendData(static):\n"
                file_content += "    output_bytes=b''\n"
                file_content += "    return static, output_bytes\n"
                file_content += "\n"
                file = open(scritp_file, "w") 
                file.write(file_content)
                file.close()

                log("Response module created")

            # Import module
            sys.path.append(args.module_path)
            try:
                module = __import__(module_name)
                #fp, pathname, description = imp.find_module(module_name)
                #module = imp.load_module(module_name, fp, pathname, description)
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
            log("%s Lanzado" % threading.currentThread().getName())

            # Initialize variables
            last_error=""
            frame=b""
            reader_module = module
            last_module_hash = getModuleHash()
            last_module_update = getModuleLastUpdate()
            reload_module_count = 0
            elapsed_time = time.time()

            # Init static data
            shared_data = {}
            try:
                shared_data = reader_module.initStaticData()
                log("init static dada ok")
            except:
                log("Error init static dada", "error")
                pass
            def checkStaticValues(tag, default_value):
                if tag not in shared_data:
                    shared_data[tag] = default_value
            checkStaticValues("id", args.id)
            checkStaticValues("enable", True)
            checkStaticValues("enable_reader", True)
            checkStaticValues("print_input_raw", True)
            checkStaticValues("print_input_ascii", True)
            checkStaticValues("enable", True)
            checkStaticValues("print_input_raw", args.print_input_raw)
            checkStaticValues("print_input_ascii", args.print_input_ascii)
            checkStaticValues("print_input_processed_raw", args.print_input_processed_raw)
            checkStaticValues("print_input_processed_ascii", args.print_input_processed_ascii)
            checkStaticValues("print_output_ascii", args.print_output_ascii)
            checkStaticValues("print_output_raw", args.print_output_raw)
            checkStaticValues("programed_task", [])
            log("Reader loaded values: %s" % shared_data)


            # Read from device
            while run:
                try:
                    # Reload module if it has changed
                    if last_module_hash != getModuleHash() or last_module_update != getModuleLastUpdate():
                        time.sleep(1)
                        reader_module = importlib.reload(reader_module)
                        last_module_hash = getModuleHash()
                        last_module_update = getModuleLastUpdate()
                        reload_module_count += 1
                        print ("- [%s] Reloaded module" % reload_module_count)

                        # try to call Reload values
                        try:
                            shared_data = reader_module.reloadStaticData(shared_data)
                            print ("- [%s] Reloaded reader module values:" % reload_module_count, shared_data)
                        except:
                            print ("! Error reloading reader values")
                            pass

                    # Check if is enable
                    if shared_data["enable"] == False or shared_data["enable_reader"] == False:
                        time.sleep(0.1)
                        continue

                    # Execute preprogramed task
                    if len(shared_data["programed_task"]) > 0:

                        # wait task
                        if type(shared_data["programed_task"][0]) is int:
                            if shared_data["programed_task"][0] < (time.time() - elapsed_time):
                                shared_data["programed_task"].remove(shared_data["programed_task"][0])
                                elapsed_time = time.time()

                        # Execute task
                        else:
                            try:
                                shared_data["programed_task"][0](shared_data)
                                print ("- Executed programed task %s" % shared_data["programed_task"][0])
                            except:
                                print ("! Error executing programed task %s" % shared_data["programed_task"][0])
                                pass

                            shared_data["programed_task"].remove(shared_data["programed_task"][0])

                    # Read data
                    byte = sim.readData()

                    # Process data
                    if byte != b"":
                        if args.print_input_raw == True and shared_data["print_input_raw"] == True:
                            log("input (hex): %s" % bytes(byte).hex(), "rx")
                        if args.print_input_ascii == True and shared_data["print_input_ascii"] == True:
                            try:
                                log("input (ascii): %s" % bytes(byte).decode('ascii'), "rx")
                            except Exception as e:
                                log(e, "error")
                        frame += bytes(byte)
                        frame_aux = frame
                        response = b""
                        shared_data, frame,response = reader_module.processData(shared_data, frame, response)
                        if last_error != "":
                            last_error = ""
                            log("Module error is fix now.", "info")
                        if frame != frame_aux:
                            if args.print_input_processed_raw == True and shared_data["print_input_processed_raw"] == True:
                                log("input* (hex): %s" % bytes(frame_aux).hex(), "rx")
                            if args.print_input_processed_ascii == True and shared_data["print_input_processed_ascii"] == True:
                                try:
                                    log("input* (ascii): %s" % bytes(frame_aux).decode('ascii'), "rx")
                                except Exception as e:
                                    print (e)
                        if response != b"":
                            if args.print_output_raw == True and shared_data["print_output_raw"] == True:
                                log("output (hex): %s" % bytes(response).hex(), "tx")
                            if args.print_output_ascii == True and shared_data["print_output_ascii"] == True:
                                try:
                                    log("output (ascii): %s" % bytes(response).decode('ascii'), "tx")
                                except Exception as e:
                                    print (e)
                            sim.sendData(response)
                except Exception as e:
                    frame=b''
                    if (run == True) and (last_error != traceback.format_exc()):
                        last_error = traceback.format_exc()
                        log(traceback.format_exc(), "error")
            log("%s Detenido" % threading.currentThread().getName())


        # Define sender thread
        def sender():
            log ("%s Lanzado" % threading.currentThread().getName())

            # Initialize variables
            last_error=""
            sender_module = module
            last_module_hash = getModuleHash()
            last_module_update = getModuleLastUpdate()
            reload_module_count = 0
            elapsed_time = time.time()

            # Init static data
            shared_data = {}
            try:
                shared_data = sender_module.initStaticData()
            except:
                pass
            shared_data['id'] = args.id
            if "enable" not in shared_data:
                shared_data["enable"] = True
            if "enable_sender" not in shared_data:
                shared_data["enable_sender"] = True
            if "module_timeout" not in shared_data:
                shared_data["module_timeout"] = 1
            shared_data["print_output_raw"] = args.print_output_raw
            shared_data["print_output_ascii"] = args.print_output_ascii
            shared_data["programed_task"] = []
            log("Sender loaded values: %s" % shared_data)


            while run:
                try:
                    # Reload module if it has changed
                    if last_module_hash != getModuleHash() or last_module_update != getModuleLastUpdate():
                        sender_module = importlib.reload(sender_module)
                        last_module_hash = getModuleHash()
                        last_module_update = getModuleLastUpdate()
                        reload_module_count += 1
                        log("[%s] Reloaded module" % reload_module_count)

                        # try to call Reload values
                        if shared_data["enable"] == True and shared_data["enable_sender"] == True:
                            try:
                                shared_data = sender_module.reloadStaticData(shared_data)
                                log("[%s] Reloaded sender module values: " % reload_module_count, shared_data)
                            except:
                                log("Error reloading sender values", "error")
                                pass

                    # Check if is enable
                    if shared_data["enable"] == False or shared_data["enable_sender"] == False:
                        continue

                    # Execute preprogramed task
                    if len(shared_data["programed_task"]) > 0:

                        # wait task
                        if type(shared_data["programed_task"][0]) is int:
                            if shared_data["programed_task"][0] < (time.time() - elapsed_time):
                                shared_data["programed_task"].remove(shared_data["programed_task"][0])
                                elapsed_time = time.time()

                        # Execute task
                        else:
                            try:
                                shared_data["programed_task"][0](shared_data)
                                print ("- Executed programed task %s" % shared_data["programed_task"][0])
                            except:
                                print ("! Error executing programed task %s" % shared_data["programed_task"][0])
                                pass

                            shared_data["programed_task"].remove(shared_data["programed_task"][0])

                    # Wait
                    time.sleep(shared_data["module_timeout"])

                    # send data
                    shared_data, output_frame = sender_module.sendData(shared_data)
                    if last_error != "":
                        last_error = ""
                        log("Module error is fix now.")
                    if output_frame != b"":
                        if args.print_output_raw == True and shared_data["print_output_raw"] == True:
                            log("output (hex): %s" % bytes(output_frame).hex(), "tx")
                        if args.print_output_ascii == True and shared_data["print_output_ascii"] == True:
                            try:
                                log("output (ascii): %s" % bytes(output_frame).decode('ascii'), "tx")
                            except Exception as e:
                                log(e, "error")
                        sim.sendData(output_frame)
                except Exception as e:
                    if (run == True) and (last_error != traceback.format_exc()):
                        last_error = traceback.format_exc()
                        log(traceback.format_exc())
            log("%s Detenido" % threading.currentThread().getName())


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
        log("\n")
        pass

    finally:
        log("Wait to threads to terminate")
        run = False
        reader_thread.join()
        sender_thread.join()


# Main execution
if __name__ == '__main__':
    sys.exit(main())

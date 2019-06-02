#!/usr/bin/python3

import argparse
import os
import sys
import serial
import pty
import subprocess
import time
import importlib
import imp


script_version="0.1.0"

def main(argv=sys.argv[1:]):

    # Parse args
    parser = argparse.ArgumentParser(
        description='Simulate communicatino end point',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '--type',
        required=False,
        default="serial",
        choices={"serial"},
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
        help='Serial port baud')
    args = parser.parse_args(argv)


    #Process args
    if args.name == "":
        args.name = args.type

    # Serial sim
    def serialSimulation():
        print('\nstarting..')
        print ("- Conexion type: %s" % args.type)

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
        print ("- Created device: %s" % device_port)


        # Generate/read responde script
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
            file_content += "# Note: is necesary to restart execution to apply any change\n"
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
            file_content += "# Note: Is NOT necesary to restart execution to apply any change.\n"
            file_content += "def processData(static, input_frame, output_frame):\n"
            file_content += "   print(\"hex: %s\\nascii: %s\\n\" % (bytes(input_frame).hex(), bytes(input_frame).decode('utf-8')))\n"
            file_content += "   input_frame = b''\n"
            file_content += "   output_frame = b''\n"
            file_content += "   return static, input_frame, output_frame\n"
            file_content += "\n"
            file_content += "\n"
            file_content += "\n"
            file_content += "# Send data each time module timeout is trigger.\n"
            file_content += "# Note: Is NOT necesary to restart execution to apply any change.\n"
            file_content += "def sendData(static):\n"
            file_content += "   output_frame=b''\n"
            file_content += "   return static, output_frame\n"
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
            return


        # Read shared data
        shared = module.static_data()


        # Catch break 
        try:
            # Generate virtual port
            cmd= ['/usr/bin/socat','-d','-d','pty,raw,echo=0,link=%s' % device_port, 'pty,raw,echo=0,link=%s' % Internal_port]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            time.sleep(1)
            print("Started!")

            ser = serial.Serial(Internal_port, args.serial_baud, rtscts=True,dsrdtr=True, timeout=0)
            err = ''
            out = ''

            # Blucke
            frame=b""
            newpid = os.fork()
            while True:
                try:
                    # Reload module
                    imp.reload(module)

                    # send process
                    if newpid == 0:
                        # Wait
                        time.sleep(shared.module_timeout)

                        # send data
                        shared, output_frame = module.sendData(shared)
                        if output_frame != b"":
                            ser.write(output_frame)

                    # Receive process
                    else:
                        # Read from device
                        while True:
                            byte = ser.read()
                            if byte == b"":
                                break
                            frame += byte

                        # Process data
                        if frame != b"":
                            response = b""
                            shared, frame,response = module.processData(shared, frame, response)
                            if response != b"":
                                ser.write(response)

                except Exception as e:
                    print ("error: '%s' -> %s" % (scritp_file, e))


        except KeyboardInterrupt:
            pass
        finally:
            proc.terminate()
            print('\nTerminated!')


    # execute connection type
    if args.type == "serial":
        return serialSimulation()


if __name__ == '__main__':
    sys.exit(main())
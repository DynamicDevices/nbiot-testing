import serial
import time
import binascii

_attached = False
_rxbuffer = ""
_debug = True

def write_data(port, txdata):
    global _debug

    if _debug:
        try:
            print('>' + txdata.decode())
        except:
            pass

    port.write(txdata + b'\r' + b'\n')
    port.flush()

def read_response(port):
    rxdata = port.read_all()
    return rxdata

def write_data_wait_response(port, txdata):
    
    global _attached
    global _rxbuffer
    global _debug
 
    write_data(port, txdata)

    # Need a timeout here
    while True:
        try:
            _rxbuffer += read_response(port).decode()
        except:
            pass

        # Work out state from responses
        if _rxbuffer.find('+CEREG:0,2') >= 0:
            _attached = False
        if _rxbuffer.find('+CEREG:0,1') >= 0:
            _attached = True
        if _rxbuffer.find('+CEREG:0,5') >= 0:
            _attached = True

        # Ended with OK or ERROR
        if _rxbuffer.find("OK\r\n") >= 0:
            if _debug:
                print('<' + _rxbuffer)
            _rxbuffer = ""
            return True
        elif _rxbuffer.find("ERROR\r\n") >= 0:
            if _debug:
                print('<' + _rxbuffer)
            _rxbuffer = ""
            return False
    
def do_vodafone_ack_test(port):
    #remoteIP = b'78.31.109.10'
    #string remotePort = b'10000'

    # Vodafone Internal ACK server
    remoteIP = b'13.79.174.161'
    remotePort = b'4123'

    print('Transmitting')

    success = write_data_wait_response(port, b'AT+NSOST=0,' + remoteIP + b',' + remotePort + b',2,AB30')

    time.sleep(1)
    
    print('Receiving')

    success = write_data_wait_response(port, b'AT+NSORF=0,3')

    time.sleep(1)

def do_node_red_test(port):

    remoteIP = b'78.31.109.10'
    remotePort = b'4123'

    idx = 0

    while True:

        idx += 1

        print('Transmitting')

        txData = b'Hello NB-IoT World! Number: ' + str(idx).encode()  + b'\r\n'
        
        hexString = binascii.hexlify(txData)

        success = write_data_wait_response(port, b'AT+NSOST=0,' + remoteIP + b',' + remotePort + b',' + str(len(txData)).encode() + b',' + hexString)

        time.sleep(1)

        print('Receiving')

        success = write_data_wait_response(port, b'AT+NSORF=0,128')

        time.sleep(1)

#                if(_lastRxMessage != txData)
#                {
#                    print("*** ACK ERROR ***")
#                }


def main(portname):

    global _attached

    print('NB-IoT Test Application - Dynamic Devices 2017')

    # Open up the serial port

    port = serial.Serial(portname, 9600)
    port.timeout = 5000;
    port.set_buffer_size(1024,1024)

    print('Opened port ' + port.name)

    # Initialise NB-IOT modem
    
    # - test for module presence
    success = write_data_wait_response(port, b'AT')

    # - reset it
    success = write_data_wait_response(port, b'AT+NRB')

    # - get the firmware version
    success = write_data_wait_response(port, b'AT+CGMR')

    # - set the IMEI (debug only)
    success = write_data_wait_response(port, b'AT+NTSETID=1,863703030044338')

    # - turn the radio on
    success = write_data_wait_response(port, b'AT+CFUN=1')

    # - connect?
    success = write_data_wait_response(port, b'AT+CSCON=1')

    # - get signal strength
    success = write_data_wait_response(port, b'AT+CSQ?')

    # - get the IMSI
    success = write_data_wait_response(port, b'AT+CIMI')

    # - get the frequency band (e.g. 8 or 20)
    success = write_data_wait_response(port, b'AT+NBAND?')

    # - get general configuration parameters
    success = write_data_wait_response(port, b'AT+NCONFIG?')

    success = write_data_wait_response(port, b'AT+CGSN=1')

    # - attach
    success = write_data_wait_response(port, b'AT+CGATT=1')

    # - set operator (?)
    success = write_data_wait_response(port, b'AT+COPS=1,2,"23591"')
    

    # - return cell stats
    success = write_data_wait_response(port, b'AT+NUESTATS')
 
    # - wait for attached status
    while not _attached:
        success = write_data_wait_response(port, b'AT+CEREG?')
        time.sleep(1)
        
    print('Attached')

    # Setup APN
    success = write_data_wait_response(port, b'AT+CGDCONT=1,"IP","vdf"')

    # Ping
    host = b'89.200.136.37'
    # success = write_data_wait_response(port, b'AT+NPING=' + host)
            
    # Setup socket

    localPort = b'4123'
    success = write_data_wait_response(port, b'AT+NSOCR=DGRAM,17,' + localPort)

    while True:
        # Do Vodafone local echo server test (responds with ACK)
        #do_vodafone_ack_test(port)

        # Test against Node Red server (responds with e.g. RxD bytes)
        do_node_red_test(port)
# Run!
main('com4')

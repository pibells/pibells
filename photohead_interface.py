# Python class for handling the Photohead interface

import serial
import logging
import datetime

class photohead_interface:
    """ Class to handle interaction with the Photohead interface
    """
    def __init__( self, device_name ):
        """ Create the class with the device name
        """
        self.device_name = device_name
        self.con = None
        
        #Photohead delay information
        #These are only loaded if required
        self.num_supported_bells = 12 #This is fixed, but duplicated in the main code
        self.delays_loaded = False
        self.current_delays = [0]*self.num_supported_bells
        
        #Flag to say if the request for the delays has been sent
        self.awaiting_delays = False
        #Will store the time of the initial request, to allow it to timeout
        self.awaiting_time = None
        self.bytes_for_delays = ( self.num_supported_bells + 1 )
        self.photohead_response_time_s = 5
        self.delay_end_marker = 255 #0xFF
        
        #The range of delays is from 1-250
        self.min_delay = 1
        self.max_delay = 250
        
        self.logger = logging.getLogger("PiBells")
        
    
    def connect( self ):
        """  Connect to the photohead interface
            Returns True if successfully connected, False otherwise
        """
        try: 
            self.con = serial.Serial( self.device_name , 2400, timeout=0)
            value  = "\n\pi_bells\n\r By David Bagley 2019\n\r"
            self.con.write(bytes(value,'UTF-8'))
        except serial.serialutil.SerialException as e:
            self.logger.error("Unable to open serial port (" + self.device_name + "): " + str(e) )
            self.con = None
            return False
        return True
    
    def ascii_code_to_bell_number( self, ascii_code ):
        """ Convert the ASCII code to a bell number
            1-9 for bells 1-9
            0   for bell 10
            E   for bell 11
            T   for bell 12
            Invalid input returns 0
        """
        if ascii_code == 48: #ASCII 0
            bell = 10
        elif ascii_code == 69: #ASCII E
            bell = 11
        elif ascii_code == 84: #ASCII T
            bell = 12
        #Handle the digits 1-9
        elif ascii_code >= 49 and ascii_code <= 57:
            bell = ascii_code - 49 + 1
        else:
            #unexpected data - log this?
            self.logger.info("Unexpected ASCII code to convert of %d",ascii_code)
            bell = 0
        return bell
    
    def get_bell( self ):
        """ Get the next bell input from the serial connection
            Bells are read as ASCII characters from the serial connection, with the values
            1-9 for bells 1-9
            0   for bell 10
            E/e for bell 11
            T/t for bell 12
            If no input is available, then return 0
        """
        
        #In case of failed serial opening
        if self.con is None:
            return 0
        
        bytesToRead = self.con.inWaiting()
        if bytesToRead == 0:
            return 0
        
        if self.awaiting_delays:
            #Data available and awaiting the delays
            self.logger.debug("Awaiting delays in the get_bell function")
            self.process_photohead_delays()
            return 0
        
        #Data available so read a single byte here and convert to a number
        data = ord( self.con.read(1) )
        
        self.logger.debug("Read data %d",data)
        
        bell = self.ascii_code_to_bell_number( data )

        self.logger.debug("Reading returning bell %d",bell)
        return bell
        
    def read_delays_from_photohead( self ):
        """ Initiates the loading of the delays from the photohead box
            Delays are only loaded if they haven't already been loaded since start up
        """
        if self.delays_loaded:
            return
        
        #In case of failed serial opening
        if self.con is None:
            #Don't set the waiting to True
            return
        
        #Request the data, using the byte 0xFE
        self.con.write( bytes.fromhex("FE") )
        self.awaiting_delays = True
        self.awaiting_time = datetime.datetime.now()
        return

    def process_photohead_delays( self ):
        """ Once the photohead delays have been requested, the next available data should be the delays
            Process the data to the currently loaded delays
            Should not reach here if `self.con` is not valid, so don't add an explicit check
        """
        #Extra check, but shouldn't get here if not
        if not self.awaiting_delays:
            return 
        
        bytes_to_read = self.con.inWaiting()
        if bytes_to_read is not self.bytes_for_delays:
            time_diff = datetime.datetime.now() - self.awaiting_time
            if time_diff.total_seconds() > self.photohead_response_time_s:
                self.logger.info("Timed out waiting for the photohead delays after waiting for %d seconds, the bytes available are %d", self.photohead_response_time_s,bytes_to_read)
                self.awaiting_delays = False
            return
        
        #Data available so read it here
        bytes_read = self.con.read( self.bytes_for_delays )
        
        #Check the last byte read was 255, indicating the end of delays
        #If not, give up as message must be corrupted with a bell sound
        if bytes_read[self.bytes_for_delays-1] is not self.delay_end_marker:
            logging.warning("Error reading in delays from photohead. Expected message to terminate in %d, but got %d. Message discarded", self.delay_end_marker , bytes_read[self.bytes_for_delays-1] )
            #Stop waiting for photohead
            self.awaiting_delays = False
            return
        
        data = [0]*self.num_supported_bells
        for idx in range(0,self.num_supported_bells):
            data[idx] = bytes_read[idx]
        
        self.logger.info("Read the following delays from the photohead: 1. %d; 2. %d; 3. %d; 4. %d; 5. %d; 6. %d; 7. %d; 8. %d; 9. %d; 10. %d; 11. %d; 12. %d;",
            data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10], data[11])
        
        #Store the delays and set the flag
        for idx in range(0,self.num_supported_bells):
            self.current_delays[idx] = data[idx]
        
        self.delays_loaded = True
        self.awaiting_delays = False
        return
    
    def set_delay( self, bell_number, delay ):
        """ Set the delay for the given bell as the current one
            bell_number - the bell number (1-self.num_supported_bells (12)) to write the delay for
            delay - the delay to write (in 100ms)
        """
        
        if bell_number < 1 or bell_number > self.num_supported_bells:
            self.logger.error("Unable to set delay for bell %d, it is out of the range: %d - %d", bell_number, 1, self.num_supported_bells )
            return
        
        #Set the new delay value, and cap to to be in range
        self.current_delays[bell_number-1] = delay
        self.current_delays[bell_number-1] = max( self.current_delays[bell_number-1], self.min_delay )
        self.current_delays[bell_number-1] = min( self.current_delays[bell_number-1], self.max_delay )
        
        self.logger.info("Setting the current delay for bell %d to %d (requested %d)", bell_number, self.current_delays[bell_number-1], delay )
        return
    
    def get_delays( self ):
        """ Get the current delays in a vector
        """
        return self.current_delays()
    
    def write_delays_to_photohead( self ):
        """ Write the delays stored locally to the photohead box 
            Delays are only written if they have already been loaded (to avoid overwriting the current settings)
            Shouldn't get here if `self.con` is invalid
            Returns True is the delays written, False if delays couldn't be written
        """
        if not self.delays_loaded:
            self.logger.info("Unable to write the delays to the photohead, they have not been loaded yet")
            return False
        
        global current_delays
        
        self.logger.info("Writing the following delays to the photohead: 1. %d, 2. %d, 3. %d, 4. %d, 5. %d, 6. %d, 7. %d, 8. %d, 9. %d, 10. %d, 11. %d, 12. %d",
            self.current_delays[0], self.current_delays[1], self.current_delays[2], self.current_delays[3], self.current_delays[4], self.current_delays[5],
            self.current_delays[6], self.current_delays[7], self.current_delays[8], self.current_delays[9], self.current_delays[10], self.current_delays[11])
        
        #Send the data
        list_to_send = list( self.current_delays )
        list_to_send.append( int("FF", 16) )
        bytes_to_send = bytes( list_to_send )
        self.con.write( bytes_to_send )
        
        #No response so don't wait for one
        return True
    
    def increase_delay( self, bell_number ):
        """ Increase the delay by 1 for the given bell number
            Limited to 250
        """
        self.logger.debug("Increasing delay for bell %d from %d to %d", bell_number, self.current_delays[bell_number-1], self.current_delays[bell_number-1] +1 );
        self.current_delays[bell_number-1] = min( self.current_delays[bell_number-1] + 1, self.max_delay )
    
    def decrease_delay( self, bell_number ):
        """ Decrease the delay by 1 for the given bell number
            Limited to 1
        """
        self.logger.debug("Decreasing delay for bell %d from %d to %d", bell_number, self.current_delays[bell_number-1], self.current_delays[bell_number-1] -1 );
        self.current_delays[bell_number-1] = max( self.current_delays[bell_number-1] - 1, self.min_delay )
    
from time import sleep

#Logging and file name establishment
import inspect
import os
import logging
import logging.handlers

#Shutting down
import datetime

#Keyboard interaction
import keyboard

# Photohead interface
from pibells.configuration import Configuration
from pibells.photohead.photohead_interface import photohead_interface

# Bell sounds
from bell_sound_player import bell_sound_player, valid_peal

# Demo playing
from pibells_demo import pibells_demo

__config = None

logger = logging.getLogger("PiBells") 

#Define the globals so the keyboard hooks can use them
all_bell_sounds =[] #All the loaded bell sounds
bell_sounds = [] #The currently selected bell sounds
valid_peals = []
muted_bells = [] #toggle to 1 to mute

#Timers
power_down_time_s = 3
restart_time_s = 3

keep_looping_flag = 1

photohead_response_time_s = 5
awaiting_photohead_delays = False
awaiting_photohead_time = 0

#Setup the global reference to the photohead class object
photohead = None

#Setup the bell sounds player class object
bell_sounds = None

pb_demo = None



all_bell_file_names = [
    "twx0",
    "twx1",
    "twx1b",
    "twx1s",
    "twx2",
    "twx3",
    "twx3b",
    "twx4",
    "twx4b",
    "twx5",
    "twx6",
    "twx6b",
    "twx7",
    "twx7b",
    "twx8",
    "twx8b",
    "twx9",
    "twx10",
    "twx11",
    "twx12",
    ]

class timed_command:
    """ Class to manage the flags for a "timed" (quick press) command
    """
    def __init__( self, time_s, name ):
        """ Create the class
        """
        self.timeout_s = time_s
        self.timeout_active = False
        self.timer = None   #Store the time the timeout began
        self.name = name
    
    def activate( self ):
        """ Activate the timer.
            If the timer was already active, checks if within the timeout, and returns true if so
            If the timer is not active, then it activates the timer
        """
        if not self.timeout_active:
            self.timeout_active = True;
            self.timer = datetime.datetime.now()
            return False
        
        #If here, then the timer was active
        diff = ( self.timer + datetime.timedelta(seconds = self.timeout_s) ) - datetime.datetime.now()
        logger.debug("The " + self.name + " time difference between the threshold and now is " + str( diff ) )
        
        if ( self.timer + datetime.timedelta(seconds = self.timeout_s) ) > datetime.datetime.now():
            #Then activated twice within the timeout
            logger.info( self.name + " request complete");
            self.timeout_active = False #reset the flag
            return True
        
        #Then the timeout has passed, reset the flag
        logger.info( self.name + " request expired");
        self.timeout_active = False
        return False
        
    def check( self ):
        """ Checks the timer to see if it has expired.
            If so, the active flag is reset, so the next time it doesn't need three presses to activate
        """
        if not self.timeout_active:
            return
        
        if ( self.timer + datetime.timedelta(seconds = self.timeout_s) ) < datetime.datetime.now():
            self.timeout_active = False
    
    def active( self ):
        """ Return True if active, false otherwise
        """
        return self.timeout_active
    
shutdown_timeout = timed_command( power_down_time_s, "power down" )
restart_timeout = timed_command( restart_time_s, "restart" )

def define_valid_peals( ):
    """ Define the different peals of bells that sounds correct
        Returns an array of valid_peal classes, ready to be configured
    """
    valid_peals = list()
    valid_peals.append( valid_peal( "D",  ["twx1",  "twx2",  "twx3",  "twx4",  "twx5",  "twx6",  "twx7",  "twx8",  "twx9",  "twx10", "twx11", "twx12", ] ) )
    valid_peals.append( valid_peal( "E",  ["twx0",  "twx1",  "twx1b", "twx3",  "twx4",  "twx4b", "twx6",  "twx7",  "twx8",  "twx8b", "twx10", "twx11", ] ) )
    valid_peals.append( valid_peal( "F#", ["twx1s", "twx1b", "twx3",  "twx3b", "twx4b", "twx6",  "twx7",  "twx7b", "twx8b", "twx10", ] ) )
    valid_peals.append( valid_peal( "G",  ["twx1",  "twx2",  "twx3",  "twx4",  "twx5",  "twx6b", "twx7",  "twx8",  "twx9", ] ) )
    valid_peals.append( valid_peal( "G#", ["twx1b", "twx2",  "twx3b", "twx4b", "twx6",  "twx6b", "twx7b", "twx8b", ] ) )
    valid_peals.append( valid_peal( "A",  ["twx1",  "twx1b", "twx3",  "twx4",  "twx5",  "twx6",  "twx7",  "twx8",  ] ) )
    valid_peals.append( valid_peal( "A#", ["twx1s", "twx1",  "twx2",  "twx3b", "twx4b", "twx5",  "twx6b", "twx7b", ] ) )
    valid_peals.append( valid_peal( "B",  ["twx0",  "twx1s", "twx1b", "twx3",  "twx4",  "twx4b", "twx6",  "twx7",  ] ) )
    valid_peals.append( valid_peal( "C",  ["twx1",  "twx2",  "twx3b", "twx4",  "twx5",  "twx6b", ] ) )
    valid_peals.append( valid_peal( "C#", ["twx1s", "twx1b", "twx3",  "twx3b", "twx4b", "twx6",  ] ) )
    valid_peals.append( valid_peal( "D",  ["twx0",  "twx1",  "twx2",  "twx3",  "twx4",  "twx5",  ] ) )
    return valid_peals

def CheckBellForMuting( bell ):
    """ Check if the absolute bell number in being muted
        Return 0 if bell should be muted
        Return bell if bell should play
    """
    global muted_bells
    
    if muted_bells[ bell-1 ]:
        return 0
    return bell

def ResetMutedBells():
    """ Reset the muted bells array to be all 0s
        i.e. no bells muted
    """
    global muted_bells, __config
    muted_bells = [0]*__config.num_bells

def GetKeyboardBellNumber():
    """ Get the number of the bell that is being pressed by the keyboard
        This uses the keyboard.is_pressed function as the scan codes for the numbers are
        different for top row and num-pad
        If no matching input is found, returns 0 or number in 1-12
        This is expected when using the multi-key combinations
    """
    if keyboard.is_pressed("1"):
        bell = 1
    elif keyboard.is_pressed("2"):
        bell = 2
    elif keyboard.is_pressed("3"):
        bell = 3
    elif keyboard.is_pressed("4"):
        bell = 4
    elif keyboard.is_pressed("5"):
        bell = 5
    elif keyboard.is_pressed("6"):
        bell = 6
    elif keyboard.is_pressed("7"):
        bell = 7
    elif keyboard.is_pressed("8"):
        bell = 8
    elif keyboard.is_pressed("9"):
        bell = 9
    elif keyboard.is_pressed("0"):
        bell = 10
    elif keyboard.is_pressed("e") or keyboard.is_pressed("−"):
        bell = 11
    elif keyboard.is_pressed("t") or keyboard.is_pressed("="):
        bell = 12
    else:
        bell = 0
    return bell

def GetKeyboardUpDown():
    """ Get the up/down key that is being pressed
        This uses the keyboard.is_pressed function as the scan codes for the numbers are
        different for top row and num-pad
        Returns +1 if the up arrow is pressed
        Returns -1 if the down arrow is pressed
        Returns 0 if neither arrow pressed
    """
    if keyboard.is_pressed("up arrow"):
        return +1
    elif keyboard.is_pressed("down arrow"):
        return -1
    else:
        return 0

def ApplyLoggingLevel( play_confirmation ):
    """ Set the logging level, with optional confirmation sound
    """
    
    if __config.logging_debug:
        logger.setLevel(logging.DEBUG)
        logger.info("Logging level set to DEBUG")
        
        if play_confirmation:
            global bell_sounds
            bell_sounds.play_reference_bell(__config.num_bells)
    else:
        logger.setLevel(logging.INFO)
        logger.info("Logging level set to INFO")

def HandleMuting():
    """ Handle the case of muting a bell
        Will attempt to get the bell number and set the flag
        Will often fire once when the mute key is pressed, then again when the number is pressed
    """
    global muted_bells
    
    bell = GetKeyboardBellNumber()
    
    if not bell:
        return
    
    #Set the flag
    muted_bells[bell-1] = 1
    logger.info("Setting bell %d to muted", bell)

def HandleUnMuting():
    """ Handle the case of un-muting a bell
        Will attempt to get the bell number and set the flag
        Will often fire once when the un-mute key is pressed, then again when the number is pressed
    """
    global muted_bells
    
    bell = GetKeyboardBellNumber()
    
    if not bell:
        return
    
    #Set the flag
    muted_bells[bell-1] = 0
    logger.info("Setting bell %d to un-muted", bell)

def HandleTenor():
    """ Handle the case of setting the tenor bell
        Will attempt to get the bell number and set the flag
        Will often fire once when the tenor key is pressed, then again when the number is pressed
    """
    global bell_sounds, __config
    
    bell = GetKeyboardBellNumber()
    
    if not bell:
        return
    
    #Set the flag
    logger.info("Setting tenor bell to %d", bell)
    bell_sounds.select_tenor( bell )
    
    #Play the sound to confirm the setting
    bell_sounds.play_bell( bell )
    
    __config.WriteConfigFile()

def HandleKey():
    """ Handle the case of setting the key of the tenor bell
        Will attempt to get the key character and set the value accordingly
        Will often fire once when the "key" key is pressed, then again when the note is pressed
    """
    global bell_sounds, __config
    
    key_direction = GetKeyboardUpDown()
    if key_direction == 0:
        #nothing to do
        return
    
    new_key_index = bell_sounds.get_valid_peal_index() + key_direction
    
    #Now clamp the key index between the ranges we have and set the new key index
    #The key index is now used to get the bells 
    bell_sounds.select_valid_peal( bell_sounds.limit_valid_peal_index( new_key_index ) )
    
    #Play the tenor bell sound
    bell_sounds.play_bell( bell_sounds.get_tenor() )
    
    __config.WriteConfigFile()

def HandleReset():
    """ Will handle when the reset key has been pressed
        Resets all bells to unmuted, the tenor to 12 and the key to the lowest
    """
    global muted_bells, __config
    ResetMutedBells()
    
    global bell_sounds
    bell_sounds.select_valid_peal( 0 )
    bell_sounds.play_bell(__config.num_bells)
    
    logger.info("All settings reset")

def HandleLogging():
    """ Toggle the logging level between debug and info
        When setting to debug, play a sound to indicate this
    """
    global __config
    __config.logging_debug = not __config.logging_debug
    
    ApplyLoggingLevel( True )
    __config.WriteConfigFile()

def HandlePlay():
    """ Handle the toggling of the play mode
    """
    global __config
    __config.play_mode = not __config.play_mode
    
    logger.info("Setting play mode to %s", __config.play_mode)
    __config.WriteConfigFile()

def HandleDelayChange( faster_flag ):
    """ Handle the case of reducing or increasing the programmed delay for a given bell
        Will attempt to get the bell number and change the delay
        Will often fire once when the "faster"/"slower" key is pressed, then again when the number is pressed
        Input is    True if the bell should sounder faster, 
                    False if the bell should sounder slower
    """    
    bell = GetKeyboardBellNumber()
    
    if not bell:
        return
    
    global photohead
    photohead.read_delays_from_photohead()
    
    #Update the current delay
    if faster_flag:
        photohead.decrease_delay( bell )
    else:
        photohead.increase_delay( bell )
    
    #Write the settings back to the device
    photohead.write_delays_to_photohead()
    
    #Write the current settings to the config?
    
    #Play the sound to confirm the change
    global bell_sounds
    bell_sounds.play_reference_bell( bell )

def HandleDefaultDelay():
    """ Handle setting the given bell to the default value
        Will attempt to get the bell number and change the delay
        Will often fire once when the keys are pressed and then again when the number is pressed
    """
    bell = GetKeyboardBellNumber()
    
    if not bell:
        return
    
    global photohead
    photohead.read_delays_from_photohead()
    photohead.set_delay( bell, __config.default_delays[bell-1] )
    
    #Write the settings back to the device
    photohead.write_delays_to_photohead()
    
    #Play the sound to confirm the change
    global bell_sounds
    bell_sounds.play_reference_bell( bell )

def HandleQuit( quit_pressed ):
    """ Test if first or second press and if the timer has expired
        If quit has been pressed, then input is true, otherwise
        it is false and it is for updating the requested flag (for clarity)
    """
    
    global shutdown_timeout
    
    if quit_pressed:
        if shutdown_timeout.activate( ):
            #Then do the shutdown
            logger.info("Power down request completed - shutting down");
            os.system("/home/pi/pibells/shutdown_script.sh &")
            #Actually close the program
            global keep_looping_flag
            keep_looping_flag = 0
    else:
        #Quit not pressed, just update the state of the timer
        shutdown_timeout.check()

def HandleRestartPiBells( restart_pressed ):
    """ Test if first or second press and if the timer has expired
        If restart has been pressed, then input is true, otherwise
        it is false and it is for updating the requested flag (for clarity)
    """
    
    global restart_timeout
    
    if restart_pressed:
        if restart_timeout.activate( ):
            #Then do the restart
            logger.info("Restart request completed - restarting application");
            os.system("/home/pi/pibells/restart_script.sh &")
            #Actually close the program
            global keep_looping_flag
            keep_looping_flag = 0
    else:
        #Quit not pressed, just update the state of the timer
        restart_timeout.check()
    
def HandleDemo():
    """ Handle the playing of a demo
    """
    global pb_demo
    global bell_sounds
    
    bell = GetKeyboardBellNumber()
    if not bell:
        return
    pb_demo.stop() #just in case it was already running
    bell_index = bell-1
    pb_demo = pibells_demo( bell_sounds, 0.2, __config.place_notation_array[bell_index] )
    
    pb_demo.start()
    
def KeyboardCallback( event ):
    """ Callback for all keyboard presses
        Pressing a single bell value 1-9,0, e(-), t(=) will play the bell
        m + bell    will mute that bell number (always)
        u + bell    will unmute that bell number (but may not play if above the tenor)
        h + bell    will set that bell as the tenor
        f + bell    will make the bell sound 100th of a second earlier 
                    (reduce the delay programmed into the photohead box)
        s + bell    will make the bell sound 100th of a second later 
                    (increase the delay programmed into the photohead box)
        d + bell    will set the delay to the default delay (loaded from the config)
        r           will clear all the current settings (tenor and muting)
        l           will toggle debug logging on/off
        k + up/down will set the bells to be a ring of 12 in D (down) to a ring of 6 in D (up) through
                    6 in D
                    6 in C#
                    6 in C
                    8 in B
                    8 in A#
                    8 in A
                    8 in G#
                    9 in G
                    10 in F#
                    12 in E
                    12 in D
        p           will toggle the playing of sounds when the bell numbers/letters are pressed
        q           shut down the application and power off the Pi
                    this needs to be pressed twice 3 seconds
        z           restart the application (quicker than the Pi)
                    this needs to be pressed twice in 3 seconds
        w + bell    start the selected demo playing until one of the normal bell keys is pressed
        See: https://github.com/boppreh/keyboard#keyboard.on_press
    """
    logger.debug( "Keyboard callback with value: %d and name %s", event.scan_code, event.name )

    global pb_demo

    #Handle special cases:
    if keyboard.is_pressed("m"):
        HandleMuting()
    elif keyboard.is_pressed("u"):
        HandleUnMuting()
    elif keyboard.is_pressed("h"):
        HandleTenor()
    elif keyboard.is_pressed("r"):
        HandleReset()
    elif keyboard.is_pressed("l"):
        HandleLogging()
    elif keyboard.is_pressed("k"):
        HandleKey()
    elif keyboard.is_pressed("p"):
        HandlePlay()
    elif keyboard.is_pressed("d"):
        HandleDefaultDelay()
    elif keyboard.is_pressed("f"):
        HandleDelayChange(True)
    elif keyboard.is_pressed("s"):
        HandleDelayChange(False)
    elif keyboard.is_pressed("q"):
        HandleQuit(True)
    elif keyboard.is_pressed("z"):
        HandleRestartPiBells(True)
    elif keyboard.is_pressed("w"):
        HandleDemo()
    else: #Try and get the bell number
        #Play the bell based on the selected tenor and key
        bell = GetKeyboardBellNumber()
        if bell and __config.play_mode:
            global bell_sounds
            bell_sounds.play_bell( bell )
        pb_demo.stop()



#Start the logging
def start_logging( file_name ):
    """ Start the logger, with rotating file handlers of 200kb, 5 files maximum
    """
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(levelname)s:%(message)s')
    handler = logging.handlers.RotatingFileHandler(file_name, maxBytes=200000, backupCount=5) #files sizes of 200kb
    handler.setFormatter(formatter)
    logger.addHandler(handler)

def main():
    global __config

    filename = inspect.getframeinfo(inspect.currentframe()).filename
    path = os.path.dirname(os.path.abspath(filename))
    log_file = path + os.path.sep + "pibells.log"
    __config = Configuration(path + os.path.sep + "pibells.ini")
    sounds_dir = path + os.path.sep + "sounds"
    
    start_logging( log_file )
    
    logger.info("========================================")
    logger.info("Starting Pi Bells - loading config")
    
    global bell_sounds
    bell_sounds = bell_sound_player()
    bell_sounds.load_sound_files( sounds_dir, all_bell_file_names )
    bell_sounds.load_valid_peals( define_valid_peals() )
    
    __config.ReadConfigFile()
    __config.LoadConfigFile()
    ApplyLoggingLevel( False )
    
    logger.info("Starting Pi Bells")
    
    global photohead
    photohead = photohead_interface(__config.device_name)
    #Could check for success, but doesn't really matter
    photohead.connect()

    bell_sounds.select_valid_peal(__config.key_index)
    bell_sounds.select_tenor( __config.num_bells )
    
    #Setup the demo
    global pb_demo
    pb_demo = pibells_demo( bell_sounds, 0.2 )
    
    #Hook to keyboard DOWN events
    #If no keyboard attached, this errors
    #Presumably, if keyboard plugged in later this will not work...
    try:
        keyboard.on_press( KeyboardCallback )
    except AttributeError:
        #Probably no keyboard attached
        logger.info("Unable to attached keyboard hook, keyboard probably not connected.")
        logger.info("Keyboard commands will not work")
    except:
        #All other errors
        logger.exception("Error attaching the keyboard callback")
        return
        
    
    global muted_bells
    ResetMutedBells()
    
    global shutdown_timeout
    global restart_timeout
    global keep_looping_flag
    
    while keep_looping_flag:
        
        #Check for user pressing quit
        if shutdown_timeout.active():
            quit_pressed = False
            HandleQuit( quit_pressed )
        
        if restart_timeout.active():
            restart_pressed = False
            HandleRestartPiBells( restart_pressed )
        
        bell = photohead.get_bell()
        if not bell:
            sleep(0.01)
            continue
        
        bell = CheckBellForMuting( bell )
        if not bell:
            continue
        
        bell_sounds.play_bell( bell )
    
    logger.info("Exiting main loop and closing program");

#This is the function that will run
if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt, stopping")
    except:
        logger.exception("Error running PiBells")

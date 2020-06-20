# Python class for handling the demonstration sounds
# - playing methods without needing an input

import threading
from time import sleep
from place_notation_processor import place_notation_processor

class place_notation:
    """ Class (structure) to hold the place notation and add_tenor flag
    """
    def __init__( self, pn_string = None, add_tenor = False ):
        """ Create the place_notation class with the bell file name and pygame sound object
        """
        self.string = pn_string
        self.add_tenor = add_tenor

class pibells_demo:
    """ Class to play different methods without needing the serial interface
        This is intended for demonstrations
    """
    def __init__( self, bell_sounds, delay_between_bells_s, place_notation_object = place_notation() ):
        """ Create the pibells_demo class and prepare for use
            bell_sounds, reference to the bell sounds object for playing the sounds
            delay_between_bells_s, the delay between bells ringing
            place_notation, the place notation (method definition) class to play, or None
        """
        self.bell_sounds = bell_sounds
        self.delay_between_bells_s = delay_between_bells_s
        self.place_notation = place_notation_object
        
        self.keep_playing = False
        
        self.timer = None
        
        self.pnp = place_notation_processor( self.place_notation.string, self.place_notation.add_tenor )
    
    def start( self ):
        """ Start the demonstration
        """
        self.pnp.reset()
        self.keep_playing = True
        
        self.play()
    
    def play( self ):
        """ Play the next bell in the sequence
        """
        #Get the next bell to play
        bell = self.pnp.get_next_bell()
        
        self.bell_sounds.play_bell( bell )
        
        if self.keep_playing:
            self.timer = threading.Timer( self.delay_between_bells_s, self.play )
            self.timer.start()
            pass
    
    def stop( self ):
        """ Stop the playing
        """
        self.keep_playing = False
        if self.timer is not None:
            self.timer.cancel()
        
        
        
# Python class for handling playing of bell sounds

import os
import pygame
import pygame.mixer as mixer
import logging
import datetime
from time import sleep

class bell_sound:
    """ Class (structure) to hold the bell sounds and file names
        This is to make setting up of the different peals more flexible
    """
    def __init__( self, file_name, sound ):
        """ Create the bell class with the bell file name and pygame sound object
        """
        self.file_name = file_name
        self.sound = sound
    
    def get_sound( self, name ):
        """ Return the sound object if it matches the file name, otherwise return None
        """
        if self.file_name == name:
            return self.sound
        return None

class valid_peal:
    """ Class (structure) to hold a valid peal of bells and the key it is in
    """
    def __init__( self, key_str, file_names ):
        """ Setup an instance with the key and list of file names
            These will be used later for loading the file and using the specific key
        """
        self.key = key_str
        self.file_names = file_names
        self.bell_sounds = None
        
        self.logger = logging.getLogger("PiBells")
    
    def configure_sounds( self, bell_sounds ):
        """ Configure the vector of bell sounds for this peal from the overall
            vector of bell_sound objects
            Note: only storing the sound object, not the bell_sound objects
        """
        self.bell_sounds = list() #clear the list
        for name in self.file_names:
            for bell in bell_sounds:
                sound = bell.get_sound( name )
                if sound is None:
                    continue
                #Sound has been found, stop searching
                break
            
            if sound is None:
                self.logger.info("Unable to find sound for file name " + name + ". Blanking sound")
            
            #Append the sound anyway, if it wasn't found then None is added, and will not be played
            self.bell_sounds.append( sound )

class bell_sound_player:
    """ Class to handle playing the bell sounds
    """
    def __init__( self ):
        """ Create the class with the device name
        """
        #Start the sounds
        pygame.mixer.pre_init(22050, -16, 1, 64)
        pygame.mixer.init()
        pygame.init() #Is this needed?
        
        #expect a maximum of 12 bells, allow 24 concurrent channels, after which the old sounds will be stopped and the channel reused
        pygame.mixer.set_num_channels(24)
        
        #Delay to wait after playing the sound - this helps keep the sound stable
        self.post_sound_wait_s = 0.01;
        
        self.logger = logging.getLogger("PiBells")
        
        #Store all the loaded bell sounds
        self.all_bell_sounds = list()
        
        #Store the valid peals
        self.valid_peals = list()
        
        #Store the currently selected valid_peal for ease of access
        self.current_bell_sounds = None
        self.valid_peal_index = None #None selected by default, forces a selection to be made
        
        #Set the tenor
        self.tenor = None
        
    def load_sound_files( self, path, sound_file_names ):
        """ Load all the given sound files and store them in an array of `bell_sounds`
            path - the path to load the files from
            sound_file_names - the list of sound file names to load (without the `.wav` extension)
        """
        self.logger.info("Loading bell sounds")
        self.all_bell_sounds = list() #clear any old sounds
        
        for name in sound_file_names:
            full_file_name = path + os.path.sep + name + '.wav'
            sound = pygame.mixer.Sound( full_file_name )
            self.all_bell_sounds.append( bell_sound( name, sound ) )
    
    def load_valid_peals( self, valid_peals ):
        """ Load an array of valid_peal objects in the order they can be selected
            Lowest peal first, highest peal last
        """
        self.logger.info("Configuring valid peal sounds for %d valid peals", len( valid_peals ) );
        self.valid_peals = valid_peals
        for peal in self.valid_peals:
            peal.configure_sounds( self.all_bell_sounds )
    
    def limit_valid_peal_index( self, valid_peal_index ):
        """ Take the new valid peal index and make sure it is limited to the range of possible valid peals
        """
        if valid_peal_index < 0:
            valid_peal_index = 0
        if valid_peal_index >= len( self.valid_peals ):
            valid_peal_index = len( self.valid_peals ) - 1
        return valid_peal_index
    
    def select_valid_peal( self, valid_peal_index ):
        """ Setup the current bells based on the valid_peal_index
        """
        if valid_peal_index < 0 or valid_peal_index >= len( self.valid_peals ):
            self.logger.error("Invalid key (valid peal) index (%d) for number of valid peals (%d). Sounds unmodified", valid_peal_index, len( self.valid_peals ) );
            return
        
        self.logger.info("Setting key to %s with index %d", self.valid_peals[ valid_peal_index ].key, valid_peal_index )
        self.valid_peal_index = valid_peal_index
        self.current_bell_sounds = self.valid_peals[ valid_peal_index ].bell_sounds
    
    def get_valid_peal_index( self ):
        """ Get the current valid peal index
        """
        return self.valid_peal_index
    
    def select_tenor( self, tenor ):
        """ Select which bell (raw bell number) will be the tenor
            tenor - the tenor to use in the range 1 - 12
        """
        self.tenor = tenor
        
        #Play the sound to indicate the selection
        self.play_bell( tenor )
    
    def get_tenor( self ):
        """ Get the currently set tenor
        """
        return self.tenor
    
    def map_bell_to_selected_peal( self, bell ):
        """ Convert the absolute bell number to bell number relative to the selected tenor
            Prevents any bell beyond the tenor ringing
            Prevents any bell below the currently selected peal ringing
            Returns the converted bell index in the bell_sounds vector, returning None if the bell should not ring
        """
        if bell > self.tenor:
            #Then can't play this
            return None
        
        curr_num_bells = len( self.current_bell_sounds )
        
        offset_from_tenor = self.tenor - bell #this should be >= 0 based on the check above
        bell_sound_index = curr_num_bells - offset_from_tenor - 1

        # prevent any bells below the current sound index from ringing
        if bell_sound_index < 0:
            return None
        self.logger.debug("Mapping bell %d to index %d with %d bell sounds",bell,bell_sound_index,curr_num_bells )
        return bell_sound_index
    
    def play_bell( self, bell ):
        """ Play the given bell index
            bell should be an integer as read from the input device (no mapping), in the range 1-12
        """
        #Map the bell to the current peal
        bell_index = self.map_bell_to_selected_peal( bell )
        
        if bell_index is None:
            return
        self.logger.debug("Playing sound index %d",bell_index)
        pygame.mixer.find_channel(True).play( self.current_bell_sounds[bell_index] )
        sleep( self.post_sound_wait_s ) #a tiny wait to give the system time to sync up
    
    def play_reference_bell( self, bell ):
        """ Play the given bell index as one of the 12, used to indicate an acceptance of a command
            bell should be an integer as read from the input device (no mapping), in the range 1-12
        """
        if bell is None:
            return
        #Convert from a bell to an index
        bell_index = bell - 1
        self.logger.debug("Playing reference sound index %d",bell_index)
        pygame.mixer.find_channel(True).play( self.valid_peals[ 0 ].bell_sounds[ bell_index ] )
        sleep( self.post_sound_wait_s ) #a tiny wait to give the system time to sync up

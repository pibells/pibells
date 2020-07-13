# Python class for handling place notation and generating the next bell to play

class place_notation_processor:
    """ Class to process a place notation string to generate the bells to play in sequence
        This is intended for demonstrations
    """
    def __init__( self, place_notation_str = None, add_tenor = False ):
        """ Create the place_notation_processor class and prepare for use
            place_notation_str, the place notation string to use, None results in rounds
            add_tenor, if there are an odd number of bells, add a tenor to cover
        """
        self.place_notation_str = place_notation_str
        self.add_tenor = add_tenor
        self.tenor_added = False #might not be an odd number of bells
        
        #Set the defaults
        self.num_bells = 0
        self.bells_array = []
        
        self.bell_index = 0
        self.row_index = 0
        self.changes_count = 0
        self.new_change = True #indicate a new change has started
        
        self.process_to_array()
    
    def reset( self ):
        """ Reset the position in the changes to start at rounds again
        """
        self.bell_index = 0
        self.row_index = 0
        self.changes_count = 0
        self.new_change = True #indicate a new change has started
        
        self.bells_array = range( 1, self.num_bells+1 )
        
    def process_to_array( self ):
        """ Convert the place notation string into an array of commands for each change
        """
        if self.place_notation_str is None:
            self.num_bells = 12
            self.place_notation_array = [ range( 0, self.num_bells ) ] #every bell stays where it is, index offset to be 0 based
            self.bells_array = range( 1, self.num_bells+1 )
            return
        
        #Parse the string to get the changes necessary
        max_bell_index = 0
        curr_fixed_bells = [-1] #an invalid index that will have no impact on the outcome, but can't append empty items
        self.place_notation_array = []
        for idx in range(0, len( self.place_notation_str ) ):
            if self.place_notation_str[idx].lower() == 'x':
                #All change
                if len( curr_fixed_bells ) > 1:
                    #write the current row if there are entries (if not, may be first)
                    self.place_notation_array.append( list(curr_fixed_bells) )
                    curr_fixed_bells = [-1]
                self.place_notation_array.append( list(curr_fixed_bells) )
            elif self.place_notation_str[idx].lower() == '.':
                #New row - store current and reset
                self.place_notation_array.append( list(curr_fixed_bells) )
                curr_fixed_bells = [-1]
            elif self.place_notation_str[idx].lower() == '-':
                #Reverse what we already have, not including the last item in the array so far
                self.place_notation_array.append( list(curr_fixed_bells) )
                curr_fixed_bells = [-1]
                #Generate a range from len-2, to -1, stepping by -1
                for idx in range( len(self.place_notation_array)-2, -1, -1 ):
                    self.place_notation_array.append( list(self.place_notation_array[idx]) )
                
            else:
                #Get the bell index (number-1), handling 0, E, T for 10, 11, 12
                bell_index = self.get_bell_index_from_char( self.place_notation_str[idx] )
                if bell_index is None:
                    #Log the error
                    continue
                curr_fixed_bells.append( bell_index )
                
                if bell_index > max_bell_index:
                    max_bell_index = bell_index
        
        #Add in the last row if populated
        if len( curr_fixed_bells ) > 0:
            self.place_notation_array.append( list(curr_fixed_bells) )
        
        self.num_bells = max_bell_index + 1
        
        #Check for adding a tenor to an odd number of bells
        if self.add_tenor and ( self.num_bells % 2 ):
            self.num_bells += 1
            self.tenor_added = True
        
        self.bells_array = range( 1, self.num_bells+1 )
    
    def print_place_notation( self ):
        """ Print the place notation for debugging
        """
        print("The place notation string is: ",self.place_notation_str)
        for idx in range( 0, len(self.place_notation_array) ):
            print("row: ", (idx+1), " - ", end = '')
            for idx_bell in range( 0, len( self.place_notation_array[idx] ) ):
                #print(self.place_notation_array[idx])
                if self.place_notation_array[idx][idx_bell] is -1 and len( self.place_notation_array[idx] ) is 1:
                    print("x ", end = '' )
                    continue
                print(self.map_bell_index_to_char( self.place_notation_array[idx][idx_bell] ), " ", end = '' )
            print("")
    
    def map_bell_index_to_char( self, bell_index ):
        """ Return the char character for the given bell index
        """
        if bell_index is 11:
            return "T"
        if bell_index is 10:
            return "E"
        if bell_index is 9:
            return "0"
        if bell_index >= 0 and bell_index <= 8:
            return str( ( bell_index+1) )
        return ""
    
    def get_bell_index_from_char( self, character ):
        """ Convert a character to a bell index
            Converts 1-9 to bells 1-9, and 0, E, T to 10, 11 and 12
            The index is then 1 less than the bell number
        """
        bell = 0 #unset
        if character.lower() == 'e':
            bell = 11
        elif character.lower() == 't':
            bell = 12
        elif  character == '0':
            bell = 10
        elif character >= '1' and character <= '9':
            bell = int( character )
        
        if bell != 0:
            return bell - 1
        
        return None
    
    def handle_new_change( self ):
        """ Check to see if we need to move to a new change and handle everything necessary
        """
        if self.bell_index < self.num_bells:
            #nothing to do
            return
        
        #reset to the start of the next change
        self.bell_index = 0
        
        #increment the changes count
        self.changes_count += 1
        
        #Flag new change
        self.new_change = True
        
        #move to the next row
        self.row_index += 1
        if self.row_index >= len( self.place_notation_array ):
            #Reset to the start of the lead
            self.row_index = 0
        
        #calculate the next row
        self.calculate_next_change()
    
    def get_next_bell( self ):
        """ Get the next bell to be played
            returns the bell index (0 to num_bells-1), or -1 at the end of a change to create a delay
        """
        #Leave a gap at the hand stroke lead
        if self.new_change and (self.changes_count % 2) == 0:
            #If a new change and a hand stroke, leave a gap of 1 bell
            bell = -1
            self.new_change = False
        else:
            bell = self.bells_array[ self.bell_index ] 
        
        self.bell_index += 1
        self.handle_new_change()
        
        return bell
        
    def calculate_next_change( self ):
        """ Permute the bells based on the current row in the place notation
            Handles having two changes of rounds at the start
        """
        if self.changes_count < 2:
            #Do nothing
            return
        
        new_bells = [0] * self.num_bells
        
        bells_to_remain = self.place_notation_array[ self.row_index ]
        #If the tenor is to be fixed, then always add it to the fixed list
        if self.tenor_added:
            bells_to_remain.append( self.num_bells - 1 )
        
        #If a two bells are to be fixed, then both will be mentioned
        #Will assume that can always swap with a bell higher
        
        #Flag to indicate if this is the first index of a swap (True) where a swap happened, or not (False)
        first_swap = True
        for idx in range( 0, self.num_bells ):
            if idx in bells_to_remain:
                new_bells[idx] = self.bells_array[ idx ]
                pass
            else:
                #Swap with the correct bell
                #print("index ",idx," is swapped")
                if first_swap:
                    new_bells[idx] = self.bells_array[ idx + 1 ]
                    first_swap = False
                else:
                    new_bells[idx] = self.bells_array[ idx - 1 ]
                    first_swap = True
        
        #Store the bells back in the class
        self.bells_array = list(new_bells)
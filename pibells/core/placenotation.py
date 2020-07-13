class place_notation:
    """ Class (structure) to hold the place notation and add_tenor flag
    """
    def __init__( self, pn_string = None, add_tenor = False ):
        """ Create the place_notation class with the bell file name and pygame sound object
        """
        self.string = pn_string
        self.add_tenor = add_tenor

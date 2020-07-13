import configparser
import logging

from pibells.core.placenotation import place_notation


class Configuration:

    def __init__(self, filename):
        self.__config = configparser.ConfigParser()
        self.__config_file = filename

        self.__logger = logging.getLogger("PiBells")

        self.bell_sounds = None
        self.logging_debug = False  # default to no debug logging, as this can cause problems with playing the sound
        self.play_mode = True
        self.device_name = "/dev/ttyUSB0"  # USB port based
        # self.device_name = "/dev/ttyS0"  # Wired serial port/ Rpi version with RS232 to TTL converter
        self.num_bells = 12  # this is duplicated in the photohead_interface
        self.default_delays = [1] * self.num_bells  # Store the default delays (min value of 1) - these are loaded from the config file

        # Store the loaded place notations, set the defaults, up to 12
        self.num_place_notations = 12
        self.place_notation_array = [
            place_notation("x16x16x16x16x16x16", False),  # Plain hunt on 6
            place_notation("5.1.5.1.5-125", False),  # Plain bob doubles, no covering tenor
            place_notation("5.1.5.1.5-125", True),  # Plain bob doubles, with covering tenor
            place_notation("x16x16x16-12", True),  # Plain bob minor, no covering tenor (wouldn't work anyway)
            place_notation("5.1.5.3.5-125", True),  # Results in St Simon's Bob Doubles, with covering tenor
            place_notation("X14X16X16-12", False),  # Results in Single Oxford Bob Minor
            place_notation("7.3.1.3.1.3", True),  # Results in Erin triples with a cover
            place_notation("X14X36X58X18-18", False),  # Results in Double Norwich Court Bob Major
            place_notation("3.1.9.1.9.1.9.1.9.1.9.1.9.1.9.1.9.1", True),  # Results in Grandsire caters with covering tenor
            place_notation("X30X14X50X16X1270X38X14X50X16X90-12", False),  # Results in Yorkshire Royal
            place_notation("3.1.E.3.1.3-1", True),  # Results in Stedman cinques
            place_notation("X1TX14-12", False),  # Results in Little Bob Max
        ]

        self.tenor = None
        self.key_index = 0 # 0 is 12 bells in D

    def ReadConfigFile(self):
        configsLoaded = self.__config.read(self.__config_file)
        if len(configsLoaded) != 1:
            # print "Unable to load config file"
            self.__logger.info("Unable to load config file - creating default")

            # Create default config file
            self.WriteConfigFile()

    def WriteConfigFile(self):

        try:
            cfgfile = open(self.__config_file, 'w')
        except:
            self.__logger.info("Unable to open config file for writing")
            return

        if not self.__config.has_section("settings"):
            self.__config.add_section('settings')

        self.__config.set('settings', 'tenor', str(self.bell_sounds.get_tenor()))
        self.__config.set('settings', 'key', str(self.bell_sounds.get_valid_peal_index()))
        self.__config.set('settings', 'logging_debug', str(self.logging_debug))
        self.__config.set('settings', 'play_mode', str(self.play_mode))
        self.__config.set('settings', 'device_name', self.device_name)

        if not self.__config.has_section("delays"):
            self.__config.add_section('delays')

        self.__config.set('delays', 'bell_1', str(self.default_delays[0]))
        self.__config.set('delays', 'bell_2', str(self.default_delays[1]))
        self.__config.set('delays', 'bell_3', str(self.default_delays[2]))
        self.__config.set('delays', 'bell_4', str(self.default_delays[3]))
        self.__config.set('delays', 'bell_5', str(self.default_delays[4]))
        self.__config.set('delays', 'bell_6', str(self.default_delays[5]))
        self.__config.set('delays', 'bell_7', str(self.default_delays[6]))
        self.__config.set('delays', 'bell_8', str(self.default_delays[7]))
        self.__config.set('delays', 'bell_9', str(self.default_delays[8]))
        self.__config.set('delays', 'bell_10', str(self.default_delays[9]))
        self.__config.set('delays', 'bell_11', str(self.default_delays[10]))
        self.__config.set('delays', 'bell_12', str(self.default_delays[11]))

        if not self.__config.has_section("demo"):
            self.__config.add_section('demo')

        for idx_place_notation in range(0, len(self.place_notation_array)):
            place_notation_name = "place_notation_" + str(idx_place_notation + 1)
            add_tenor_name = "add_tenor_" + str(idx_place_notation + 1)
            self.__config.set('demo', place_notation_name, str(self.place_notation_array[idx_place_notation].string))
            self.__config.set('demo', add_tenor_name, str(self.place_notation_array[idx_place_notation].add_tenor))

        self.__config.write(cfgfile)
        cfgfile.close()


    def ConfigSectionMap(self, section):
        # From: https://wiki.python.org/moin/ConfigParserExamples
        dict1 = {}
        options = self.__config.options(section)
        for option in options:
            try:
                dict1[option] = self.__config.get(section, option)
                if dict1[option] == -1:
                    pass  # DebugPrint("skip: %s" % option)
            except:
                # print("exception on %s!" % option)
                dict1[option] = None
        return dict1


    def LoadConfigFile(self):
        self.__logger.info("Loading config file")

        try:
            tenor = self.ConfigSectionMap("settings")['tenor']
            if tenor is not None:
                self.tenor = int(tenor)
                self.__logger.info("Loaded tenor as %d", tenor)

            key_index = self.ConfigSectionMap("settings")['key']
            if key_index is not None:
                self.key_index = int(key_index)
                self.__logger.info("Loaded key_index as %d", key_index)

            logging_debug = self.ConfigSectionMap("settings")['logging_debug']
            if logging_debug is not None:
                if logging_debug.lower() == 'true':
                    self.logging_debug = True
                else:
                    self.logging_debug = False
                self.__logger.info("Loaded logging debug as %s", logging_debug)

            play_mode = self.ConfigSectionMap("settings")['play_mode']
            if play_mode is not None:
                if play_mode.lower() == 'true':
                    self.play_mode = True
                else:
                    self.play_mode = False
                self.__logger.info("Loaded play mode as %s", play_mode)

            device_name = self.ConfigSectionMap("settings")['device_name']
            if device_name is not None:
                self.device_name = device_name
                self.__logger.info("Loaded device name is %s", device_name)

            # Load the default delays
            for idx in range(0, 12):
                default_delay = self.ConfigSectionMap("delays")['bell_' + str(idx + 1)]
                if default_delay is not None:
                    self.default_delays[idx] = int(default_delay)
                else:
                    self.__logger.info("Unable to load default delay for bell %d from the config", (idx + 1))

            self.__logger.debug(
                "Loaded the following default delays from the ini file: 1. %d, 2. %d, 3. %d, 4. %d, 5. %d, 6. %d, 7."
                " %d, 8. %d, 9. %d, 10. %d, 11. %d, 12. %d",
                self.default_delays[0], self.default_delays[1], self.default_delays[2], self.default_delays[3],
                self.default_delays[4], self.default_delays[5], self.default_delays[6], self.default_delays[7],
                self.default_delays[8], self.default_delays[9], self.default_delays[10], self.default_delays[11])

            # Load the demos to play - check they are present
            place_notation = self.ConfigSectionMap("demo")['place_notation_1']
            if place_notation is not None:
                # Load all the configs we have
                # Clear the current place notations as loading new ones
                self.place_notation = []

                for idx_place_notation in range(0, self.num_place_notations):
                    place_notation_name = "place_notation_" + str(idx_place_notation + 1)
                    add_tenor_name = "add_tenor_" + str(idx_place_notation + 1)

                    place_notation = self.ConfigSectionMap("demo")[place_notation_name]
                    add_tenor_str = self.ConfigSectionMap("demo")[add_tenor_name]

                    if place_notation is None or add_tenor_str is None:
                        self.__logger.info("Error loading place notation at %d, this will be dropped", idx_place_notation)
                    else:
                        if add_tenor_str.lower() == 'true':
                            add_tenor = True
                        else:
                            add_tenor = False
                        self.place_notation_array.append(place_notation(str(place_notation), add_tenor))

        except Exception as e:
            self.__logger.exception("Error loading config file")
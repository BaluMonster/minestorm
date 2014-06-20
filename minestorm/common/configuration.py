#!/usr/bin/python3
import json
import minestorm

class ConfigurationManager:
    """
    Class which manage minestorm configuration entries
    """

    def __init__(self):
        self._entries = {}

    def load(self, *files, flush=True):
        """ Load the configuration from a file """
        # If the flush argument is set to True, flush
        # old configuration entries
        if flush:
            self.flush()
        # Load all files
        for file_name in files:
            entries = self._load_file(file_name) # First load that file
            self._entries = self._merge_entries(self._entries, entries) # After merge its content with the global entries dict

    def _load_file(self, file_name):
        """ Load a specific file and return its entries """
        # Open the file and decode its content as json
        with open(file_name, "r") as f:
            entries = json.load(f)
        # If an 'include' list is present in the root of the configuration file
        # include all its values
        if 'include' in entries:
            for extra_file in entries['include']:
                extra_entries = self._load_file(extra_file) # Load extra entries
                entries = self._merge_entries(entries, extra_entries) # Merge new entries with old ones
        # Now return the flatted version of all entries
        return self._flat_entries(entries)

    def _flat_entries(self, entries, prefix=""):
        """
        Convert the multi-level structure of the configuration in a flatted one

        entries['a']['b']['c'] -> entries['a.b.c']
        Lists and lists' content will not be flatted
        """
        result = {}
        # Iterate over entries
        for key, value in entries.items():
            # If the value is a dict, flat it also
            if type(value) == dict:
                new_value = self._flat_entries(value, prefix+key+'.') # Call _flat_entries recursively
                result.update(new_value) # Merge new values
            else:
                result[prefix+key] = value # Add the key to the result
        return result

    def _merge_entries(self, old, new):
        """ Merge old entries with new ones - needed for good flat entries merge """
        # Differences between standard merge:
        # - Merge also lists, tuples and sets
        result = old
        # Iterate over new items
        for key, value in new.items():
            # If the value type is list, tuple or set merge it
            # Can be done only if the type of the new entry is the same as the value of the old entry
            if key in old and type(value) in (list, tuple, set) and type(value) == type(result[key]):
                result[key] = old[key] + value
            else:
                result[key] = value # Else update it normally
        return result

    def get(self, key, default=None):
        """ Get a configuration entry """
        try:
            # Try to return the value
            return self._entries[key]
        # If the key isn't in the entries dict
        except KeyError:
            # If a default value was provided return it
            if default != None:
                return default
            # Else re-raise the KeyError
            raise

    def update(self, key, value):
        """ Update a configuration value """
        self._entries[key] = value

    def remove(self, key):
        """ Remove an entry from the configuration """
        del self._entries[key]

    def has(self, key):
        """ Check if a key is present in the entries dict """
        return key in self._entries

    def flush(self):
        """ Flush all configuration entries """
        self._entries = {}

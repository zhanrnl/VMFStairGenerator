#-------------------------------------------------------------------------------
# Name:        StairGenerator
# Purpose:     Generates stairs lol
#
# Author:      Lennart
#
# Created:     05/07/2011
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import re, pprint
from collections import OrderedDict

class StairGenerator():
    vmf_filename = ""
    vmf_data = ""
    vmf_list = []
    pp = pprint.PrettyPrinter()

    def __init__(self, vmf_filename):
        self.vmf_filename = vmf_filename
        vmf_file = open(self.vmf_filename, 'r')
        self.vmf_data = vmf_file.read()
        self.tokenize_vmf_data()

    def tokenize_vmf_data(self):
        # TODO: make tokenize rely on syntactic elements rather than whitespace
        self.vmf_list = self.vmf_data.strip().replace("\t", "").split("\n")

    def dict_from_vmf(self, vmf_list):
        """Turns vmf_list into a python dict woo"""
        output = OrderedDict()
        # stack of the current block object to be adding keyvalues to
        cur_obj = []
        cur_obj.append(output)
        for token in vmf_list:
            if token[0] == '"': # keyvalue pair
                split = token.split('"')
                cur_obj[-1][split[1]] = split[3]
            elif token[0] == '}': # end of a block
                cur_obj.pop()
            elif token[0] != '{': # start of a block
                new_obj = OrderedDict()
                # to figure out where to put the new object if duplicates
                # if there are multiple blocks with same name, we need to store
                # all of them in a list under that one dict key
                if token in cur_obj[-1]: # block already exists! grrrr
                    # check if we've already made it into list
                    if type(cur_obj[-1][token]) is not list:
                        cur_obj[-1][token] = [cur_obj[-1][token]]
                    cur_obj[-1][token].append(new_obj)
                else:
                    cur_obj[-1][token] = new_obj
                cur_obj.append(new_obj)
        return output

    def find_templates(self):
        """Finds stairs template brushes in vmf"""
        vmf = self.dict_from_vmf(self.vmf_list)

def main():
    generator = StairGenerator("stairstest.vmf")
    generator.find_templates()

if __name__ == '__main__':
    main()

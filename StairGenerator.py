#-------------------------------------------------------------------------------
# Name:        StairGenerator
# Purpose:     Generates stairs and doesn't afraid of anything
#
# Author:      Lennart
#
# Created:     05/07/2011
#-------------------------------------------------------------------------------
#!/usr/bin/env python

import re
from collections import OrderedDict

class StairGenerator():
    """Functions for easy creation of stairs in Valve map files. Loads a VMF,
    generates stairs from template brushes in the VMF, and can resave the
    VMF."""

    vmf_filename = ""
    vmf_data = ""
    vmf_tokens = []
    vmf_dict = OrderedDict()

    def __init__(self, vmf_filename):
        self.vmf_filename = vmf_filename
        vmf_file = open(self.vmf_filename, 'r')
        self.vmf_data = vmf_file.read()
        self.tokenize_vmf()
        self.dictify_vmf()

    def tokenize_vmf(self):
        # TODO: make tokenize rely on syntactic elements rather than whitespace
        self.vmf_tokens = self.vmf_data.strip().replace("\t", "").split("\n")

    def dictify_vmf(self):
        """Turns vmf_tokens into a python dict woo"""
        # stack of the current block object to be adding keyvalues to
        cur_obj = []
        cur_obj.append(self.vmf_dict)
        for token in self.vmf_tokens:
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

    def write_vmf(self, vmf_filename):
        """Writes the edited vmf data to a file."""
        f = open(vmf_filename, 'w')
        f.write(self.write_vmf_level(self.vmf_dict, 0))

    def write_vmf_level(self, subdict, indent):
        """Helper for write_vmf"""
        output = ""
        for k, v in iter(subdict.iteritems()):
            if type(v) is OrderedDict:
                output += ('\t'*indent + k + '\n' + '\t'*indent + '{\n'
                    + self.write_vmf_level(v, indent+1) + '\t'*indent
                    + '}\n')
            elif type(v) is list:
                for i in v:
                    output += ('\t'*indent + k + '\n' + '\t'*indent + '{\n'
                        + self.write_vmf_level(i, indent+1) + '\t'*indent
                        + '}\n')
            else:
                output += '\t'*indent + '"' + str(k) + '" "' + str(v) + '"\n'
        return output

    def find_templates(self):
        """Finds stairs template brushes in vmf, checks based on orientation and
        texturing"""
        templates = []
        solids = self.vmf_dict['world']['solid']
        if type(solids) is not list:
            raise Exception("Can't deal with single-brush vmfs yet")
        for solid in solids:
            materials = []
            all_sides_ortho = True
            for side in solid['side']:
                materials.append(side['material'])
                if not self.side_ortho(side):
                    all_sides_ortho = False
            if self.is_template_textured(materials) and all_sides_ortho:
                templates.append(solid)
        return templates

    def is_template_textured(self, texture_list):
        """Takes a list of textures and determines if a solid is textured like
        a template brush"""
        skip_count, stairs_count = 0, 0
        for tex in texture_list:
            if tex == 'TOOLS/TOOLSSKIP':
                skip_count += 1
            elif tex == 'SIGNS/STAIRS_RED':
                stairs_count += 1
            else:
                return False
        # Only return for brushes textured all in skip except for one in
        # stairs_red
        return (skip_count, stairs_count) == (5, 1)

    def side_ortho(self, side):
        """Returns whether all points in a side lie in an orthogonal plane"""
        # turn into list of coordinate tuples
        coords = [tuple(coord.split(' ')) for coord in
            side['plane'][0:-1].replace('(', '').split(') ')]
        all_same = [0]*3
        # all three points lie in axial-oriented orthogonal plane if one coord
        # is same for all points
        for i in range(0, 3):
            all_same[i] = (coords[0][i] == coords[1][i]
                and coords[0][i] == coords[2][i])
        return sum(all_same)


def main():
    generator = StairGenerator("anglestest.vmf")
    generator.find_templates()

if __name__ == '__main__':
    main()

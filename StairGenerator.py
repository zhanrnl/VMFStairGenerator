#-------------------------------------------------------------------------------
# Name:        StairGenerator
# Purpose:     Generates stairs LOL JK it actually makes ramps
#
# Author:      Lennart
#
# Created:     05/07/2011
#-------------------------------------------------------------------------------
#!/usr/bin/env python

from numpy import array, cross, matrix, identity
from collections import OrderedDict

class StairGenerator():
    """Functions for easy creation of stairs in Valve map files. Loads a VMF,
    generates stairs from template brushes in the VMF, then resaves the VMF."""

    vmf_filename = ""
    vmf_data = ""
    vmf_tokens = []
    vmf_dict = OrderedDict()

    # default stair params (not used yet, we're only making ramps atm)
    step_length = 12
    step_height = 8 # length, height
    trim_width = 2
    construction = 0 # 0 = solid, 1 = hanging, 2 = hanging step

    # more defaults
    material = 'DEV/DEV_BLENDMEASURE2'
    uaxis = '[1 0 0 0] 0.25'
    vaxis = '[0 -1 0 0] 0.25'
    rotation = '0'
    lightmapscale = '16'
    smoothing_groups = '0'
    editor = OrderedDict([('color', '255 160 10'), ('visgroupshown', '1'),
        ('visgroupautoshown', '1')])

    def __init__(self, vmf_filename):
        self.vmf_filename = vmf_filename
        try:
            vmf_file = open(self.vmf_filename, 'r')
        except:
            print "No file found with that filename!"
            quit()
        self.vmf_data = vmf_file.read()
        self.tokenize_vmf()
        self.dictify_vmf()

    def tokenize_vmf(self):
        # TODO: make tokenize rely on syntactic elements rather than whitespace
        self.vmf_tokens = self.vmf_data.strip().replace("\t", "").split("\n")

    def dictify_vmf(self):
        """Turns vmf_tokens into a Python dict for easy accessibility of vmf
        keyvalues"""
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
                if token in cur_obj[-1]: # block already exists!
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
            if k[0] == '*':
                pass # internal data, don't write to file
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

    def generate_stairs(self):
        """Where the actual stair generation happens. Reads templates by
        find_templates, then generates stairs for each template"""
        templates = self.find_templates()
        print len(templates), "template%s found" % ("" if (len(templates) == 1)
            else "s")
        for template_num, template in enumerate(templates):
            print "\nGenerating stairs for template #", template_num+1
            sides = template['side']

            print "Adding normals to vmf data"
            self.add_normals(sides)

            print "Finding coordinate bounds of template brush"
            reg_point, dims, orientation = self.get_reg_point_dims(sides)

            # create new ordered dict for ramp
            print "Creating ramp"
            self.create_ramp(reg_point, dims, orientation)

            # delete template, so we can write the ramp brush in place
            print "Removing template brush"
            solids = self.vmf_dict['world']['solid']
            solids.remove(template)

        print "\nSaving VMF"
        self.write_vmf('stairswrite.vmf')

        print "\nAll done."

    def create_ramp(self, reg_point, dims, orientation):
        solids = self.vmf_dict['world']['solid']

        max_solid_id = max([int(solid['id']) for solid in solids])
        # Yo dawg, I herd you like list comprehensions
        max_side_id = max([max([int(side['id']) for side in sides]) for sides
            in [solid['side'] for solid in solids]])

        length, width, height = dims
        # ignore length to get stairs of a given slope, height takes priority
        length = (height * self.step_length) / self.step_height

        ramp = OrderedDict()
        ramp['id'] = max_solid_id + 1 # give ids that won't collide

        sides = []
        bottom_side = OrderedDict()
        bottom_side['*plane'] = [
            (0, width, 0),
            (0, 0, 0),
            (length, 0, 0)]
        sides.append(bottom_side)
        back_side = OrderedDict()
        back_side['*plane'] = [
            (0, 0, 0),
            (0, width, 0),
            (0, width, height)]
        sides.append(back_side)
        right_side = OrderedDict()
        right_side['*plane'] = [
            (0, width, 0),
            (length, width, 0),
            (0, width, height)]
        sides.append(right_side)
        left_side = OrderedDict()
        left_side['*plane'] = [
            (length, 0, 0),
            (0, 0, 0),
            (0, 0, height)]
        sides.append(left_side)
        slope_side = OrderedDict()
        slope_side['*plane'] = [
            (0, 0, height),
            (0, width, height),
            (length, width, 0)]
        sides.append(slope_side)

        # transform points
        print "Transforming ramp position"
        for side in sides:
            for i, point in enumerate(side['*plane']):
                # rotate
                point = self.rotate(point, orientation)
                # translate
                point = self.translate(point, reg_point)
                side['*plane'][i] = point

        # add other side info (id, default material)
        for i, side in enumerate(sides):
            side['id'] = max_side_id + i + 1
            side['plane'] = self.combine_coord_list(side['*plane'])
            self.set_to_defaults(side)

        # get rid of tuple data because it will fuck with iteritems :(
        for side in sides:
            del side['*plane']

        ramp['side'] = sides
        ramp['editor'] = self.editor
        solids.append(ramp)

    def rotate(self, point, orientation):
        if orientation == 0:
            rot_matrix = matrix(identity(3))
        elif orientation == 1:
            rot_matrix = matrix([
                [0, 1, 0],
                [-1, 0, 0],
                [0, 0, 1]])
        elif orientation == 2:
            rot_matrix = matrix([
                [-1, 0, 0],
                [0, -1, 0],
                [0, 0, 1]])
        elif orientation == 3:
            rot_matrix = matrix([
                [0, -1, 0],
                [1, 0, 0],
                [0, 0, 1]])
        point = matrix(point) * rot_matrix
        return tuple(point.tolist()[0])

    def translate(self, point, reg_point):
        return tuple([sum(i) for i in zip(point, reg_point)])

    def set_to_defaults(self, side):
        side['material'] = self.material
        side['uaxis'] = self.uaxis
        side['vaxis'] = self.vaxis
        side['rotation'] = self.rotation
        side['lightmapscale'] = self.lightmapscale
        side['smoothing_groups'] = self.smoothing_groups

    def get_reg_point_dims(self, sides):
        """Finds the registration point, dimensions, and orientation of a
        template brush."""
        # identify the front face
        front_face = [side for side in sides if side['material'] ==
            'SIGNS/STAIRS_RED'][0]
        front_normal = front_face['*normal']
        back_normal = [-num for num in front_normal]
        back_face = [side for side in sides if side['*normal']
            == back_normal][0]
        # find bounds for stairs with find_max_dir
        top = self.find_max_dir(self.parse_coord_list(front_face['plane']),
            "+z")
        bottom = self.find_max_dir(self.parse_coord_list(
            front_face['plane']), "-z")
        if front_normal == [1, 0, 0]:
            # Faces east
            front = self.parse_coord_list(front_face['plane'])[0][0]
            back = self.parse_coord_list(back_face['plane'])[0][0]
            left = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "-y")
            right = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "+y")
            orientation = 0
        elif front_normal == [0, 1, 0]:
            # Faces north
            front = self.parse_coord_list(front_face['plane'])[0][1]
            back = self.parse_coord_list(back_face['plane'])[0][1]
            left = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "+x")
            right = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "-x")
            orientation = 1
        elif front_normal == [-1, 0, 0]:
            # Faces west
            front = self.parse_coord_list(front_face['plane'])[0][0]
            back = self.parse_coord_list(back_face['plane'])[0][0]
            left = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "+y")
            right = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "-y")
            orientation = 2
        elif front_normal == [0, -1, 0]:
            # Faces south
            front = self.parse_coord_list(front_face['plane'])[0][1]
            back = self.parse_coord_list(back_face['plane'])[0][1]
            left = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "-x")
            right = self.find_max_dir(self.parse_coord_list(
                front_face['plane']), "+x")
            orientation = 3
        else:
            raise Exception('Template has bad normal')

        # registration point is origin in local coords
        if orientation % 2 == 0:
            reg_point = (back, left, bottom)
        else:
            reg_point = (left, back, bottom)
        # calculate dimensions
        length = abs(front - back)
        width = abs(left - right)
        height = top - bottom

        return reg_point, (length, width, height), orientation

    def find_max_dir(self, coords, max_dir):
        """Finds the maximum coordinate in a given direction of a set of 3D
        coordinates (that might be given through parse_coord_list). max_dir can
        be '+x', '-x', '+y', '-y', '+z', or '-z'"""
        if max_dir == '+x':
            return max([coord[0] for coord in coords])
        elif max_dir == '-x':
            return min([coord[0] for coord in coords])
        elif max_dir == '+y':
            return max([coord[1] for coord in coords])
        elif max_dir == '-y':
            return min([coord[1] for coord in coords])
        elif max_dir == '+z':
            return max([coord[2] for coord in coords])
        elif max_dir == '-z':
            return min([coord[2] for coord in coords])
        raise Exception('Bad max_dir parameter')

    def add_normals(self, sides):
        """Given a list of vmf side dicts, adds normals to each side under
        ['*normal']."""
        for side in sides:
            # figure out direction of normal
            coords = [array(coord) for coord in
                self.parse_coord_list(side['plane'])]
            vec = [] # Gah, damn you vmf, ordering points in CW order, you
            vec.append(coords[1] - coords[0]) # think using LHR is funny?
            vec.append(coords[0] - coords[2])
            side['*normal'] = [int(num/abs(num)) if num != 0 else 0 for num in
                list(cross(vec[0], vec[1]))]
            if side['*normal'][2] != 0 and (side['material'] ==
                'SIGNS/STAIRS_RED'):
                print ("Can't have STAIRS_RED on top or bottom face, " +
                    "removing template")
                templates.remove(templates.index(template))

    def find_templates(self):
        """Finds stairs template brushes in vmf, checks based on orientation and
        texturing"""
        templates = []
        solids = self.vmf_dict['world']['solid']
        if type(solids) is not list:
            solids = [solids]
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
        # stairs_red, this doesn't invalidate brushes with top or bottom in
        # stairs because we'll look at normals later
        return (skip_count, stairs_count) == (5, 1)

    def side_ortho(self, side):
        """Returns whether all points in a side lie in an orthogonal plane"""
        # turn into list of coordinate tuples
        coords = self.parse_coord_list(side['plane'])
        all_same = [0]*3
        # all three points lie in axial-oriented orthogonal plane if one coord
        # is same for all points
        for i in range(0, 3):
            all_same[i] = (coords[0][i] == coords[1][i]
                and coords[0][i] == coords[2][i])
        return sum(all_same) == 1 # modified to disallow invalid planes (with
        # zero width or height)

    def parse_coord_list(self, coords):
        """Breaks up the vmf syntax for a set of 3 coordinates into Python data
        types"""
        return [tuple([float(num) for num in coord.split(' ')]) for coord in
            coords[0:-1].replace('(', '').split(') ')]

    def combine_coord_list(self, coords):
        """The inverse function of parse_coord_list."""
        output = ''
        for coord in coords:
            output += '('
            for num in coord:
                output += (str(int(num)) + ' ')
            output = output[0:-1] + ') '
        return output[0:-1]


def main():
    generator = StairGenerator("stairstest.vmf")
    generator.generate_stairs()

if __name__ == '__main__':
    main()

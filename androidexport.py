#! /usr/bin/env python
import os.path
import subprocess

import inkex


class AndroidExport(inkex.Effect):

    def __init__(self):
        inkex.Effect.__init__(self)

        # store the path to export the image
        self.OptionParser.add_option("--path", action="store",
                                     type="string", dest="path")

        self.OptionParser.add_option("--ldpi", action="store",
                                     type="string", dest="ldpi")
        self.OptionParser.add_option("--mdpi", action="store",
                                     type="string", dest="mdpi")
        self.OptionParser.add_option("--hdpi", action="store",
                                     type="string", dest="hdpi")
        self.OptionParser.add_option("--xhdpi", action="store",
                                     type="string", dest="xhdpi")
        self.OptionParser.add_option("--xxhdpi", action="store",
                                     type="string", dest="xxhdpi")
        self.OptionParser.add_option("--xxxhdpi", action="store",
                                     type="string", dest="xxxhdpi")


        self.resolution_multipliers = {"ldpi": 0.5, "mdpi": 1,
                                       "hdpi": 1.5, "xhdpi": 2,
                                       "xxhdpi": 3, "xxxhdpi": 4}
        self.should_export          = {"ldpi": False, "mdpi": False,
                                       "hdpi": False, "xhdpi": False,
                                       "xxhdpi": False, "xxxhdpi": False}

    def effect(self):

        if not self.options.path:
            inkex.errormsg('Empty file path!')
            exit()

        for resolution in self.should_export:
            flag = getattr(self.options, resolution)
            if flag.lower() == "true":
                self.should_export[resolution] = True
            else:
                self.should_export[resolution] = False

        # Checks if a path has the correct format
        if "{}" not in self.options.path:
            inkex.errormsg('The path entered does not have a {} inside it. '
                           'Enter a path that has a {} in the place of the '
                           'resolution name. In example, if you put the path '
                           '"folder/example/{}/my_image.png", this extension '
                           'will export images for several paths: '
                           '"folder/example/mdpi/my_image.png", '
                           '"folder/example/xxhdpi/my_image.png"')
            exit()

        # Solves the paths that use "~" as the home directory
        filepath = os.path.expanduser(self.options.path)
        filepath = filepath.replace('{}', '{0}')


        area = self.get_selected_area()
        resolutions = filter(lambda res: self.should_export[res],
                             self.resolution_multipliers.keys())

        self.export_to_resolutions(filepath, area, resolutions)

    def get_selected_area(self):
        """
        Returns two pairs ((x0, y0), (x1, y1)) with the minimun
        and maximun points of the selected area.
        """

        # If there ins't any object selected raises an error
        if len(self.selected) == 0:
            inkex.errormsg('Select an object to export.')
            exit()

        # Command line to revocer all information inside the SVG file
        command = ["inkscape", "--without-gui", "--query-all", self.svg_file]

        # Running the command on terminal
        process = subprocess.check_output(command, stderr=subprocess.PIPE)

        # Processing the command output
        process = process.strip()
        process = process.split('\n')

        x1 = y1 = float('-inf')
        x0 = y0 = float('+inf')

        document_h = self.unittouu(self.document.getroot().attrib['height'])

        # For each node selected
        for node in self.selected:
            for result in process:
                # Get the result line that belongs to that node
                if node in result:
                    result = result.replace(node, "")
                    result = filter(lambda x: x != "", result.split(","))

                    w = self.unittouu(result[2])
                    h = self.unittouu(result[3])

                    x = self.unittouu(result[0])
                    y = document_h - self.unittouu(result[1]) - h

                    x0 = min(x, x0)
                    x1 = max(x + w, x1)

                    y0 = min(y, y0)
                    y1 = max(y + h, y1)

                    break

        # Only the integral part is taken from the result
        x0 = int(x0)
        x1 = int(x1)

        y0 = int(y0)
        y1 = int(y1)

        return [[x0, y0], [x1, y1]]

    def export_to_resolutions(self, filepath, area, resolutions):
        """
        For each resolution selected exports the objects that are inside the
        area.
        """

        # Make the image sizes disible by 2
        if (area[1][0] - area[0][0]) % 2:
            area[1][0] += 1
        w = area[1][0] - area[0][0]

        if (area[1][1] - area[0][1]) % 2:
            area[1][1] += 1
        h = area[1][1] - area[0][1]

        # Command Pattern to export an SVG
        pattern = 'inkscape --without-gui -a {}:{}:{}:{} -w {} -h {} -e {} {}'

        x0, y0 = area[0]
        x1, y1 = area[1]

        # For each resolution checked export the image
        for resolution in resolutions:
            multiplier = self.resolution_multipliers[resolution]

            export_w = w*multiplier
            # Granting divisibility by 2 on the final image
            if export_w % 2:
                export_w += 1

            export_h = h*multiplier
            # Granting divisibility by 2 on the final image
            if export_h % 2:
                export_h += 1

            path = filepath.format(resolution)

            # Checks if the directory exists
            if not os.path.exists(os.path.dirname(path)):
                msg = 'The directory "{}" does not exist.'
                msg = msg.format(os.path.dirname(path))
                inkex.errormsg(msg)
                exit()


            # Formating the export command
            cmd = pattern.format(x0, y0, x1, y1, export_w, export_h,
                                 path, self.svg_file)

            # Executing the export command
            process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
            process.wait()


if __name__ == "__main__":
    ext = AndroidExport()
    ext.affect()

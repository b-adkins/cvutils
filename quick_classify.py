# The following file contains open-source, non-Matlab GUIs to view images and
# crop them for training data.
#
# Copyright (C) 2016 Boone Adkins
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import collections
import matplotlib.image as mpimg
import matplotlib.lines as mlines
import matplotlib.pyplot as pyplot
import matplotlib.patches as mpatches
import numpy as np
import os
import PIL.Image
import sys


class ImageShower(object):
    def __init__(self):
        self.current_file = ''
        self.img = np.array([[]])

        self.fig, self.ax = pyplot.subplots()

    def update(self, path, subtitle=''):
        '''
        :param path: To image
        '''

        self.img = mpimg.imread(path)

        # First time
        if not self.current_file:
            self.img_plot = pyplot.imshow(self.img)
        else:
            self.img_plot.set_data(self.img)
        self.current_file = path

        self.ax.set_title(subtitle)
        self.fig.suptitle(self.current_file)
        pyplot.draw()


class SlideShow(ImageShower):
    def __init__(self, images, subtitles=None):
        super(SlideShow, self).__init__()

        self.images = images
        if subtitles is None:
            self.subtitles = np.full(len(images), '')
        else:
            self.subtitles = subtitles
        self.i_current = 0

        self.fig.canvas.mpl_connect('key_press_event', self.handle_keypress)

        self.update(images[0], subtitle=subtitles[0])

    def handle_keypress(self, event):
        if event.key == 'right':
            self.i_current = min(self.i_current + 1, len(self.images) - 1)
        elif event.key == 'left':
            self.i_current = max(0, self.i_current - 1)
        else:
            return

        self.update(self.images[self.i_current], self.subtitles[self.i_current])


class ImageClassifier(ImageShower):
    def __init__(self, files, key_to_dir):
        super(ImageClassifier, self).__init__()

        self.image_itr = files.__iter__()
        self.update(self.image_itr.next())

        self.key_to_dir = key_to_dir

        self.fig.canvas.mpl_connect('key_press_event', self.handle_keypress)

    def handle_keypress(self, event):
        if event.key == 'delete':
            self.delete_image()
        elif event.key == ' ':
            self.ax.set_title('Skipped')
        else:
            try:
                dest_dir = self.key_to_dir[event.key]
            except KeyError:
                self.ax.set_title('')
                return
            try:
                os.rename(self.current_file, os.path.join(dest_dir, self.current_file))
                self.ax.set_title('Moved {} to {}.'.format(self.current_file, dest_dir))
            except OSError as e:
                self.ax.set_title('Unable to move {}:\n{}'.format(self.current_file, e))

        self.next_image()

    def delete_image(self):
        try:
            os.remove(self.current_file)
            self.ax.set_title('Deleted {}'.format(self.current_file))
        except OSError as e:
            self.ax.set_title('Unable to deleted {}:\n{}'.format(self.current_file, e))

    def next_image(self):
        while True:
            try:
                self.update(self.image_itr.next())
                break
            except StopIteration:
                print 'Done'
                sys.exit()  # @todo Figure out a more elegant way to end the Figure
            except (OSError, IOError):
                continue

class ImageTagger(ImageClassifier):
    def __init__(self, files, key_to_dir):
        super(ImageTagger, self).__init__(files, key_to_dir)

        self.fig.canvas.mpl_connect('button_press_event', self.handle_mouse_press)
        self.fig.canvas.mpl_connect('button_release_event', self.handle_mouse_release)
        self.fig.canvas.mpl_connect('motion_notify_event', self.handle_mouse_motion)
        self.fig.canvas.mpl_connect('scroll_event', self.handle_scroll_wheel)
        self.rect_being_dragged = False

        self.colors = ['b', 'purple', 'r', 'g', 'y', 'c', 'teal']  # Color choices for rectangles
        self.rect_options = {'fill': False, 'color': self.colors[0], 'linewidth': 3}

        self.sizes = [[64, 128]]  # Possible rectangle sizes
        self.rects = []  # Tagged rectangles
        self.rect_colors = {}  # Matplotlib Patch has no "get_color()"; thus must be tracked separately
        self.color_to_dir = {color: dir for dir, color in zip(self.key_to_dir.values(), self.colors)}

        self.DONE_DIR = 'tagged'
        if not os.path.exists(self.DONE_DIR):
            os.mkdir(self.DONE_DIR)
        elif os.path.isfile(self.DONE_DIR):
            raise ValueError('Directory for tagged files cannot be created because of existing regular file. Pick a new '
                             'name.')

    def get_rect_at(self, x, y):
        '''
        Gets a rectangle at the given (x, y)
        :param x: X-coordinate, relative to image.
        :param y: Y-coordinate, relative to image.
        :return: A rectangle (first in the list) or None.
        '''
        for rect in self.rects:
            x_rect, y_rect = rect.get_xy()
            width = rect.get_width()
            height = rect.get_height()
            if (x_rect <= x < x_rect + width) and (y_rect <= y < y_rect + height):
                return rect
        return None

    def crop_rectangle(self, rect):
        x, y = rect.get_xy()
        width = rect.get_width()
        height = rect.get_height()

        # Crop each rectangle's image
        img_array = self.img[y:y+height, x:x+width]
        img_array = (img_array*255).astype(np.uint8)  # Convert from 0.0 to 1.0 to 0 to 255

        return img_array

    def save_rectangles(self):
        outfiles = []
               
        for i, rect in enumerate(self.rects): 
            img_array = self.crop_rectangle(rect)
            
            # Create output path
            file, ext = os.path.splitext(self.current_file)
            ext = ext[1:]  # Remove the leading '.'
            dir = self.color_to_dir[self.rect_colors[rect]]  # @todo Egads what a mess
            outfile = "{}_{}.{}".format(file, i, ext)
            outpath = os.path.join(dir, outfile)

            # Save
            img_obj = PIL.Image.fromarray(img_array)
            img_obj.save(outpath, format=ext)

            outfiles.append(outfile)
        self.ax.set_title('Saved {}'.format(outfiles))

    def clear_rectangles(self):
        try:
            os.rename(self.current_file, os.path.join(self.DONE_DIR, self.current_file))  # Mark tagged or skipped files "done"
        except OSError:
            print "Couldn't move image to completed folder."

        self.rect_colors = {}
        for i in range(len(self.rects))[::-1]:
            self.rects[i].remove()
            del self.rects[i]

    def next_image(self):
        self.clear_rectangles()
        super(ImageTagger, self).next_image()

    def handle_keypress(self, event):
        if event.key == 'enter':
            self.save_rectangles()
            self.next_image()
        elif event.key in [' ', 'pagedown']:
            self.next_image()
        elif event.key == 'delete':
            self.delete_image()
            self.next_image()

    def handle_mouse_press(self, event):
        if event.button == 1:
            clicked_rect = self.get_rect_at(event.xdata, event.ydata)
            if clicked_rect:
                self.rect_being_dragged = clicked_rect

    def handle_mouse_motion(self, event):
        if self.rect_being_dragged:
            self.rect_being_dragged.set_xy((event.xdata, event.ydata))
            pyplot.draw()

    def handle_scroll_wheel(self, event):
        if self.rect_being_dragged:
            rect = self.rect_being_dragged
        else:
            rect = self.get_rect_at(event.xdata, event.ydata)

        if rect:
            old_color = self.rect_colors[rect]
            print 'old color:', old_color
            i = self.colors.index(old_color)
            if event.button == 'up':
                i = (i + 1) % len(self.color_to_dir)
            elif event.button == 'down':  # Else should suffice, but... defensive programming
                i = (i - 1 + len(self.color_to_dir)) % len(self.color_to_dir)
            new_color = self.colors[i]
            rect.set_color(new_color)
            self.rect_colors[rect] = new_color
            print 'new color:', self.colors[i]
            pyplot.draw()

    def handle_mouse_release(self, event):
        print 'Mouse release:', event
        y_max, x_max, _ = self.img.shape
        if event.xdata is None or event.ydata is None:
            return

        if self.rect_being_dragged:
            if event.button == 1:
                self.rect_being_dragged = False
            else:
                # While dragging, don't register any clicks except releasing the left button
                return
        else:
            clicked_rect = self.get_rect_at(event.xdata, event.ydata)
            if clicked_rect:
                # Is in a rectangle
                if event.button == 3:
                    # Remove on right click (if not being dragged)
                    clicked_rect.remove()  # Remove from the plot
                    self.rects.remove(clicked_rect)  # Remove from the list
                    pyplot.draw()
                    return
                # elif event.button == 1:
                #     clicked_rect.set_edgecolor('g')
                #     pyplot.draw()
                #     return

            elif event.button == 1:
            # Nothing being dragged and left mouse; thus left click. Create new rectangle
                size = self.sizes[0]
                xy = [event.xdata - size[0]/2, event.ydata - size[1]/2]

                # Keep in bounds
                if xy[0] < 0:
                    xy[0] = 0
                elif xy[0] + size[0] > x_max:
                    xy[0] = x_max - size[0]

                if xy[1] < 0:
                    xy[1] = 0
                elif xy[1] + size[1] > y_max:
                    xy[1] = y_max - size[1]

                new_rect = mpatches.Rectangle(xy, size[0], size[1], **self.rect_options)
                self.rects.append(new_rect)
                self.rect_colors[new_rect] = self.colors[0]
                self.ax.add_patch(new_rect)
                pyplot.draw()

# Drag for scale
class ImageDragTagger(ImageTagger):
    def __init__(self, files, key_to_dir, aspect_ratio=0.5, margin=(0.25, 0.125)):
        '''

        :param files:
        :param key_to_dir:
        :param aspect_ratio: width/height
        :param margin:
        :return:
        '''
        super(ImageDragTagger, self).__init__(files, key_to_dir)

        self.pct_margin = (0.25, 0.125)  # 16px out of 64x128 in the original HOG paper

        self.aspect_ratio = float(self.sizes[0][0])/float(self.sizes[0][1])
        self.is_sizing_rect = False

        self.ep = 1

    def create_sizing_aid(self):
        self.sizing_line = mlines.Line2D(self.x0 + np.array([0, self.ep]), self.y0 + np.array([0, self.ep]), lw=4,
                                         color=self.colors[0])
        self.sizing_circle = mpatches.Circle((self.x0, self.y0), self.ep, **self.rect_options)
        self.ax.add_patch(self.sizing_circle)
        self.ax.add_line(self.sizing_line)

    def handle_mouse_press(self, event):
        if event.button == 1:
            clicked_rect = self.get_rect_at(event.xdata, event.ydata)
            if clicked_rect:
                self.rect_being_dragged = clicked_rect
            else:
                self.is_sizing_rect = True

                self.x0, self.y0 = event.xdata, event.ydata  # Where the drag was started
                self.rect_corner = (self.x0, self.y0)  # Offset the rectangle slightly
                self.rect_being_created = mpatches.Rectangle((self.x0, self.y0), self.ep, self.ep, **self.rect_options)
                self.rect_colors[self.rect_being_created] = self.colors[0]
                self.rects.append(self.rect_being_created)  # As its being made, it can be removed or changed category=
                self.ax.add_patch(self.rect_being_created)

                self.create_sizing_aid()

                pyplot.draw()

    def handle_mouse_motion(self, event):
        print event
        x_mouse, y_mouse = event.xdata, event.ydata
        if x_mouse is None or y_mouse is None:
            print 'event.xdata or event.ydata is None!'
            return
        if self.is_sizing_rect == True:
            h = (y_mouse - self.y0)/(1 - self.pct_margin[1])
            w = int(np.abs(h)*self.aspect_ratio)

            # Scale the margin and circle
            # m_w = self.pct_margin[0]*w
            m_h = self.pct_margin[1]*h
            r = w * self.pct_margin[0] / 2

            # Recenter the top
            self.rect_being_created.set_x(self.x0 - w/2)
            self.rect_being_created.set_y(self.y0 - m_h)
            self.rect_being_created.set_width(w)
            self.rect_being_created.set_height(h)
            self.sizing_circle.center = self.x0, self.y0 + r
            self.sizing_circle.set_radius(r)
            self.sizing_line.set_ydata([self.y0 + 2*r, y_mouse - m_h])
            pyplot.draw()
        else:
            super(ImageDragTagger, self).handle_mouse_motion(event)

    def handle_mouse_release(self, event):
        if event.button == 1:
            if self.is_sizing_rect:
                self.is_sizing_rect = False
                self.sizing_line.remove()
                self.sizing_circle.remove()
                pyplot.draw()
            if not self.rect_being_dragged or event.button == 3:
                return  # Avoids creating new rectangles in parent method

        super(ImageDragTagger, self).handle_mouse_release(event)

    def save_rectangles(self):
        super(ImageDragTagger, self).save_rectangles()  # Saves the unscaled rectangle


if __name__ == '__main__':
    '''
    USAGE:
      SCRIPT_NAME APP DIRS [FILES]

      APP - drag, tap, or whole:
        whole - classify entire images with a few keypresses
        tap - click to create a fixed sized window
        drag - drag a fixed aspect ratio window
      DIRS - comma-seperated output directories, one for each classification.
        Will be created if they don't exist.
      FILES - if given, work on these files. If not, searches current working directory.
    '''
    app = sys.argv[1]  # Git style - classify drag, classify tap, classify whole
    dirs = sys.argv[2].split(',')
    keys = ['right', 'left', 'up', 'down', 'x', 'y', 'z']
    key_to_dir = collections.OrderedDict({})
    for key, dir in zip(keys, dirs):
        key_to_dir[key] = dir
    if len(sys.argv) > 3:
        files = sys.argv[2:]
    else:
        files = [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]

    for dir in key_to_dir.values():
        if os.path.exists(dir):
            if not os.path.isdir(dir):
                print '"{}" is not a directory!'
                sys.exit(2)
        else:
            os.mkdir(dir)
            print 'Created directory "{}".'

    print 'Instructions:'
    for key, classification in key_to_dir.iteritems():
        print 'Hit {} to classify as "{}"'.format(key, classification)
    print
    # raw_input('Hit enter to continue')

    if app == 'drag':
        gui = ImageDragTagger(files, key_to_dir)
    elif app == 'tap':
        gui = ImageTagger(files, key_to_dir)
    elif app == 'whole':
        gui = ImageClassifier(files, key_to_dir)

    pyplot.show()

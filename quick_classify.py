import collections
import matplotlib.image as mpimg
import matplotlib.pyplot as pyplot
import matplotlib.patches
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

        self.sizes = [[64, 128]]  # Possible rectangle sizes
        self.rects = []  # Tagged rectangles
        self.rect_colors = {}  # Matplotlib Patch has no "get_color()"; thus must be tracked separately
        self.color_to_dir = {color: dir for dir, color in zip(self.key_to_dir.values(), self.colors)}


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

    def save_rectangles(self):
        outfiles = []
        for i, rect in enumerate(self.rects):
            x, y = rect.get_xy()
            width = rect.get_width()
            height = rect.get_height()

            # Crop each rectangle's image
            img_array = self.img[y:y+height, x:x+width]
            img_array = (img_array*255).astype(np.uint8)  # Convert from 0.0 to 1.0 to 0 to 255

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

                color = self.colors[0]
                new_rect = matplotlib.patches.Rectangle(xy, size[0], size[1], fill=False, color=color, linewidth='3')
                self.rects.append(new_rect)
                self.rect_colors[new_rect] = color
                self.ax.add_patch(new_rect)
                pyplot.draw()


# if __name__ == '__main__':
#     dirs = sys.argv[1].split(',')
#     keys = ['right', 'left', 'up', 'down']
#     key_to_dir = {}
#     for key, dir in zip(keys, dirs):
#         key_to_dir[key] = dir
#     if len(sys.argv) > 2:
#         files = sys.argv[2:]
#     else:
#         files = [f for f in os.listdir(os.getcwd()) if os.path.isfile(f)]
#
#     for dir in key_to_dir.values():
#         if os.path.exists(dir):
#             if not os.path.isdir(dir):
#                 print '"{}" is not a directory!'
#                 sys.exit(2)
#         else:
#             os.mkdir(dir)
#             print 'Created directory "{}".'
#
#     print 'Instructions:'
#     for key, classification in key_to_dir.iteritems():
#         print 'Hit {} to classify as "{}"'.format(key, classification)
#     print
#     # raw_input('Hit enter to continue')
#
#     gui = ImageClassifier(files, key_to_dir)
#
#     pyplot.show()

if __name__ == '__main__':
    dirs = sys.argv[1].split(',')
    keys = ['right', 'left', 'up', 'down']
    key_to_dir = collections.OrderedDict({})
    for key, dir in zip(keys, dirs):
        key_to_dir[key] = dir
    if len(sys.argv) > 2:
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

    gui = ImageTagger(files, key_to_dir)

    pyplot.show()

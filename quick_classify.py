import cv2
import matplotlib.image as mpimg
import matplotlib.pyplot as pyplot
import matplotlib.patches
import numpy as np
import os
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

        self.fig.canvas.mpl_connect('key_press_event', self.handle_keypress)

    def handle_keypress(self, event):
        if event.key == 'delete':
            try:
                os.remove(self.current_file)
                self.ax.set_title('Deleted {}'.format(self.current_file))
            except OSError as e:
                self.ax.set_title('Unable to deleted {}:\n{}'.format(self.current_file, e))
        elif event.key == ' ':
            self.ax.set_title('Skipped')
        else:
            try:
                dest_dir = key_to_dir[event.key]
            except KeyError:
                self.ax.set_title('')
                print
                return
            try:
                os.rename(self.current_file, os.path.join(dest_dir, self.current_file))
                self.ax.set_title('Moved {} to {}.'.format(self.current_file, dest_dir))
            except OSError as e:
                self.ax.set_title('Unable to move {}:\n{}'.format(self.current_file, e))

        # Move to next image (do-while kludge)
        while True:
            try:
                self.update(self.image_itr.next())
                break
            except StopIteration:
                print 'Done'
                sys.exit()
            except (OSError, IOError):
                continue

class ImageTagger(ImageClassifier):
    def __init__(self, files, key_to_dir):
        super(ImageTagger, self).__init__(files, key_to_dir)

        self.fig.canvas.mpl_connect('button_press_event', self.handle_click)

        self.sizes = [[64, 128]]  # Possible rectangle sizes
        self.rects = []  # Tagged rectangles

    def handle_click(self, event):
        y_max, x_max, _ = self.img.shape

        print event
        for rect in self.rects:
             x_rect, y_rect = rect.get_xy()
             width = rect.get_width()
             height = rect.get_height()
             if (x_rect <= event.xdata < x_rect + width) and (y_rect <= event.ydata < y_rect + height):
                # Is in rectangle
                if event.button == 3:
                    # Remove on right click
                    rect.remove()  # Remove from the plot
                    self.rects.remove(rect)  # Remove from the list
                    pyplot.draw()
                    return
                else:
                    rect.set_edgecolor('g')
                    pyplot.draw()
                    return

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

        rect = matplotlib.patches.Rectangle(xy, size[0], size[1], fill=False)
        self.rects.append(rect)
        self.ax.add_patch(rect)

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
    key_to_dir = {}
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

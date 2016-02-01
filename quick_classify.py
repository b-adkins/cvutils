import cv2
import matplotlib.image as mpimg
import matplotlib.pyplot as pyplot
import numpy as np
import os
import sys


class ImageShower(object):
    def __init__(self):
        self.current_image = ''

        self.fig, self.ax = pyplot.subplots()

    def update(self, path, subtitle=''):
        '''
        :param path: To image
        '''

        img = mpimg.imread(path)

        # First time
        if not self.current_image:
            self.img_plot = pyplot.imshow(img)
        else:
            self.img_plot.set_data(img)
        self.current_image = path

        self.ax.set_title(subtitle)
        self.fig.suptitle(self.current_image)
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


class ImageClassifierGUI(ImageShower):
    def __init__(self, files, key_to_dir):
        super(ImageClassifierGUI, self).__init__()

        self.image_itr = files.__iter__()
        self.update(self.image_itr.next())

        self.fig.canvas.mpl_connect('key_press_event', self.handle_keypress)

    def handle_keypress(self, event):
        if event.key == 'delete':
            try:
                os.remove(self.current_image)
                self.ax.set_title('Deleted {}'.format(self.current_image))
            except OSError as e:
                self.ax.set_title('Unable to deleted {}:\n{}'.format(self.current_image, e))
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
                os.rename(self.current_image, os.path.join(dest_dir, self.current_image))
                self.ax.set_title('Moved {} to {}.'.format(self.current_image, dest_dir))
            except OSError as e:
                self.ax.set_title('Unable to move {}:\n{}'.format(self.current_image, e))

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

    gui = ImageClassifierGUI(files, key_to_dir)

    pyplot.show()

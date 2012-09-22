#!/usr/bin/env python
# vim: set fileencoding=utf-8 :
# Andre Anjos <andre.anjos@idiap.ch>
# Wed Jun 22 17:50:08 2011 +0200
#
# Copyright (C) 2011-2012 Idiap Research Institute, Martigny, Switzerland
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, version 3 of the License.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Runs some video tests
"""

import os, sys
import tempfile
import pkg_resources
from nose.plugins.skip import SkipTest
import functools

def ffmpeg_found(test):
  '''Decorator to check if the FFMPEG is available before enabling a test'''

  @functools.wraps(test)
  def wrapper(*args, **kwargs):
    try:
      from .._io import VideoReader, VideoWriter
      return test(*args, **kwargs)
    except ImportError:
      raise SkipTest('FFMpeg was not available at compile time')

  return wrapper


def F(f):
  """Returns the test file on the "data" subdirectory"""
  return pkg_resources.resource_filename(__name__, os.path.join('data', f))

def get_tempfilename(prefix='bobtest_', suffix='.avi'):
  (fd, name) = tempfile.mkstemp(suffix, prefix)
  os.unlink(name)
  return name

# These are some global parameters for the test.
INPUT_VIDEO = F('test.mov')
OUTPUT_VIDEO = get_tempfilename()

import unittest
import numpy
import bob

class VideoTest(unittest.TestCase):
  """Performs various combined read/write tests on video files"""
  
  @ffmpeg_found
  def test01_CanOpen(self):

    # This test opens and verifies some properties of the test video available.
    # It examplifies how to directly call the VideoReader and how to access
    # some of its properties.
    v = bob.io.VideoReader(INPUT_VIDEO)
    self.assertEqual(v.height, 240)
    self.assertEqual(v.width, 320)
    self.assertEqual(v.duration, 15000000) #microseconds
    self.assertEqual(v.number_of_frames, 375)
    self.assertEqual(len(v), 375)
    self.assertEqual(v.codec_name, 'mjpeg')

  @ffmpeg_found
  def test02_CanReadImages(self):

    # This test shows how you can read image frames from a VideoReader
    v = bob.io.VideoReader(INPUT_VIDEO)
    for frame in v:
      # Note that when you iterate, the frames are numpy.ndarray objects
      # So, you can use them as you please. The organization of the data
      # follows the other encoding systems in bob: (color-bands, height,
      # width).
      self.assertTrue(isinstance(frame, numpy.ndarray))
      self.assertEqual(len(frame.shape), 3)
      self.assertEqual(frame.shape[0], 3) #color-bands (RGB)
      self.assertEqual(frame.shape[1], 240) #height
      self.assertEqual(frame.shape[2], 320) #width

  @ffmpeg_found
  def test03_CanGetSpecificFrames(self):

    # This test shows how to get specific frames from a VideoReader

    v = bob.io.VideoReader(INPUT_VIDEO)

    # get frame 27 (we start counting at zero)
    f27 = v[27]

    self.assertTrue(isinstance(f27, numpy.ndarray))
    self.assertEqual(len(f27.shape), 3)
    self.assertEqual(f27.shape, (3, 240, 320))

    # you can also use negative notation...
    self.assertTrue(isinstance(v[-1], numpy.ndarray))
    self.assertEqual(len(v[-1].shape), 3)
    self.assertEqual(v[-1].shape, (3, 240, 320))

    # get frames 18 a 30 (exclusive), skipping 3: 18, 21, 24, 27
    f18_30 = v[18:30:3]
    for k in f18_30:
      self.assertTrue(isinstance(k, numpy.ndarray))
      self.assertEqual(len(k.shape), 3)
      self.assertEqual(k.shape, (3, 240, 320))

    # the last frame in the sequence is frame 27 as you can check
    self.assertTrue( numpy.array_equal(f18_30[-1], f27) )

  @ffmpeg_found
  def test04_CanWriteVideo(self):

    # This test reads all frames in sequence from a initial video and records
    # them into an output video, possibly transcoding it.
    iv = bob.io.VideoReader(INPUT_VIDEO)
    ov = bob.io.VideoWriter(OUTPUT_VIDEO, iv.height, iv.width)
    for k, frame in enumerate(iv): ov.append(frame)
   
    # We verify that both videos have similar properties
    self.assertEqual(len(iv), len(ov))
    self.assertEqual(iv.width, ov.width)
    self.assertEqual(iv.height, ov.height)
   
    ov.close() # forces close; see github issue #6
    del ov # trigger closing of the output video stream

    iv2 = bob.io.VideoReader(OUTPUT_VIDEO)

    # We verify that both videos have similar frames
    for orig, copied in zip(iv.__iter__(), iv2.__iter__()):
      diff = abs(orig.astype('float32')-copied.astype('float32'))
      m = numpy.mean(diff)
      self.assertTrue(m < 3.0) # average difference is less than 3 gray levels
    os.unlink(OUTPUT_VIDEO)

    del iv2 # triggers closing of the input video stream

  @ffmpeg_found
  def test05_CanUseArrayInterface(self):

    # This shows you can use the array interface to read an entire video
    # sequence in a single shot
    array = bob.io.load(INPUT_VIDEO)
    iv = bob.io.VideoReader(INPUT_VIDEO)
   
    for frame_id, frame in zip(range(array.shape[0]), iv.__iter__()):
      self.assertTrue ( numpy.array_equal(array[frame_id,:,:,:], frame) )

  @ffmpeg_found
  def test06_CanIterateOnTheSpot(self):

    # This test shows how you can read image frames from a VideoReader created
    # on the spot
    for k, frame in enumerate(k, bob.io.VideoReader(INPUT_VIDEO)):
      self.assertTrue(isinstance(frame, numpy.ndarray))
      self.assertEqual(len(frame.shape), 3)
      self.assertEqual(frame.shape[0], 3) #color-bands (RGB)
      self.assertEqual(frame.shape[1], 240) #height
      self.assertEqual(frame.shape[2], 320) #width

from unittest import TestCase

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)) +
                "/../Mapping/rectangle_fitting/")

from Mapping.rectangle_fitting import rectangle_fitting as m

print(__file__)


class Test(TestCase):

    def test1(self):
        m.show_animation = False
        m.main()

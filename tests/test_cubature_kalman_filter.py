from unittest import TestCase

from Localization.cubature_kalman_filter import cubature_kalman_filter as m

print(__file__)


class Test(TestCase):

    def test1(self):
        m.show_animation = False
        m.main()

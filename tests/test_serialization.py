import json
import os
import unittest

import pytest

from adsmanparse.classic_serializer import ClassicSerializer
from adsmanparse.translator import Translator

class TestClassicSerialization(unittest.TestCase):
    def setUp(self):
        stubdata_dir = os.path.join(os.path.dirname(__file__), "stubdata/")
        self.inputdir = os.path.join(stubdata_dir, "input")
        self.outputdir = os.path.join(stubdata_dir, "output")
        self.maxDiff = None

    def test_serialization(self):
        filenames = [
            "AJ_nlm_iop_aj_162_1",
        ]

        for f in filenames:
            bibstem = f.split("_")[0].ljust(5, ".")
            print("THE BIBSTEM IS %s" % bibstem)
            test_infile = os.path.join(self.inputdir, f + ".json")
            test_outfile = os.path.join(self.outputdir, f + ".tag")

            with open(test_infile, "r") as fj:
                parsed_rec = json.load(fj)

            with open(test_outfile, "r") as ft:
                classic_rec = ft.read()

            xr = Translator()
            xr.translate(data=parsed_rec, bibstem=bibstem)
            xr.output['bibcode'] = '2021AJ....162...20N'
            cs = ClassicSerializer()
            test_output = cs.output(xr.output)
            self.assertEqual(test_output, classic_rec)


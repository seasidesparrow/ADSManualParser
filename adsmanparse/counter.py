"""
counter.py: an object to store and manipulate counter-type page number
assignments for ADS Classic bibcodes.  This intended for bibstems that use
counters to set the page, absent a page or electronic id.
"""
import json
import os

class JSONLoadException(Exception):
    pass


class JSONWriteException(Exception):
    pass


class GetPageException(Exception):
    pass


class CounterSyntaxException(Exception):
    pass


class Counter(object):

    def __init__(self):
        pass

    def _initialize_from_json(self, infile):
        if os.path.isfile(infile):
            try:
                with open(infile, "r") as fj:
                    return json.load(fj)
            except Exception as err:
                raise JSONLoadException("Failed to load bibcounter data: %s" % err)
        else:
            return {}

    def _write_to_json(self, infile, bibdict):
        try:
            with open(infile, "w") as fj:
                fj.write("%s\n" % json.dumps(bibdict))
        except Exception as err:
            raise JSONWriteException("Failed to write bibcounter data: %s" % err)

    def get_page(self, bibstem, year, infile):
        if bibstem and year and infile:
            # make sure year is a string, not integer
            year = str(year)
            try:
                bibdata = self._initialize_from_json(infile)
                if bibdata.get(bibstem, {}):
                    try:
                        page = bibdata[bibstem].pop(year)
                    except:
                        page = 0
                    newpage = page + 1
                    bibdata[bibstem][year] = newpage
                else:
                    newpage = 1
                    bibdata[bibstem]={year: newpage}
                self._write_to_json(infile, bibdata)
                return newpage
            except Exception as err:
                raise GetPageException("Counter increment failed: %s" % err)
        else:
            raise CounterSyntaxException("Call get_page with bibstem, year, and path to counter.json!")

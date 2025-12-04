import os
from datetime import date, timedelta
from glob import glob


class NoBaseDirectoryException(Exception):
    pass


class GetDatesException(Exception):
    pass


class GetLogsException(Exception):
    pass


class GetInputFilesException(Exception):
    pass


class RecentOAIPMH(object):

    # Purpose:
    #   Use configuration/user input to create a list of .xml files harvested
    #   by an instance of our OAI-PMH harvester in the past [maxage] days.
    #   For the ADS Crossref content harvest, basedir is sources/CrossRef
    #   It assumes the logs are in a subdirectory "UpdateAgent", but you
    #   can specify this when you instantiate the handler; you can also
    #   provide it with a list of one or more dates in "YYYY-MM-DD" format
    # Usage:
    #   handler = RecentOAIPMH(maxage=7, basedir='/My/Harvest/Dir/')
    #   files = handler.getxmlfiles()

    def __init__(self, maxage=7, basedir=None, logdir="UpdateAgent", dates=[]):
        if not basedir:
            raise NoBaseDirectoryException("You need to specify a base directory for your OAI-PMH Harvest")
        else:
            if type(maxage) == str:
                maxage = int(maxage)
            self.maxage = maxage
            self.basedir = basedir
            self.logdir = logdir
            self.dates = dates
            self.logfiles = []


    def _datestrings(self):
        if not self.dates:
            try:
                today = date.today()
                dates = [today.strftime("%Y-%m-%d")]
                nextdate = today
                maxage = self.maxage
                while maxage > 0:
                    maxage -= 1
                    nextdate -= timedelta(days=1)
                    dates.append(nextdate.strftime("%Y-%m-%d"))
                if dates:
                    self.dates = dates
            except Exception as err:
                raise GetDatesException("Unable to get list of dates to check: %s" % err)
    
    def _getlogfiles(self):
        logfiles = []
        logDir = os.path.join(self.basedir, self.logdir)
        try:
            for d in self.dates:
                fileExt = "*.out.%s" % d
                filenames = os.path.join(logDir, fileExt)
                logfiles.extend(glob(filenames))
            if logfiles:
                logfiles.sort()
                self.logfiles = logfiles
        except Exception as err:
            raise GetLogsException("Unable to find logfiles: %s" % err)

    def getxmlfiles(self):
        xmlfiles = []
        try:
            self._datestrings()
            self._getlogfiles()
            for f in self.logfiles:
                with open(f, "r") as fl:
                    for l in fl.readlines():
                        xmlfiles.append("%s%s" % (self.basedir, l.strip().split("\t")[0]))
            return xmlfiles
        except Exception as err:
            raise GetInputFilesException("Unable to get a list of input xml files: %s" % err)

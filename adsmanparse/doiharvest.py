from adsmanparse.exceptions import *
from habanero.cn import content_negotiation as CoNe


class DoiHarvester(object):

    def __init__(self, doi=None, recformat='crossref-xml'):
        self.doi = doi
        self.recformat = recformat

    def get_record(self):
        if self.doi:
            try:
                return CoNe(ids = self.doi, format=self.recformat)
            except Exception as err:
                raise HarvestFailException('Error fetching record for DOI=%s: %s' % (self.doi, err))
        else:
            raise NoDoiException('No DOI supplied!')

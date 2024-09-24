import itertools
import re
import string
from collections import OrderedDict
from namedentities import named_entities

re_empty_affil = re.compile(r"\w{2,3}\(\)")

class ClassicSerializer(object):
    """
    ClassicSerializer: creates a classic tagged record from a record in
    the ADS' ingest_data_model format.

    ClassicSerializer().output returns the classic-formatted record as a
    single string (including carriage returns) that can be written to a file.
    """


    def _aff_codes_generator(self):
        letters = [c for c in string.ascii_uppercase]
        two_char = ["%c%c" % (x, y) for (x, y) in \
            itertools.product(letters, letters)]
        three_char = ["%s%c" % (x, y) for (x, y) in \
            itertools.product(two_char, letters)]
        return two_char + three_char

    def _clean_string(self, data):
        data = named_entities(data)
        data = re.sub(r"&[rl]squo;", "\'", data)
        data = re.sub(r"&[rl]dquo;", "\"", data)
        data = re.sub(r"&nbsp;", " ", data)
        data = re.sub(r"&zwnj;", " ", data)
        return data

    def __init__(self, **kwargs):
        self.AFF_LABEL = self._aff_codes_generator()
        self.FIELD_DICT = OrderedDict([
            ('bibcode', {'tag': 'R'}),
            ('title', {'tag': 'T'}),
            ('authors', {'tag': 'A', 'join': '; '}),
            ('native_authors', {'tag': 'n', 'join': ', '}),
            ('affiliations', {'tag': 'F', 'join': ', '}),
            ('pubdate', {'tag': 'D'}),
            ('publication', {'tag': 'J'}),
            ('language', {'tag': 'M'}),
            ('comments', {'tag': 'X', 'join': '; '}),
            ('source', {'tag': 'G'}),
            ('copyright', {'tag': 'C'}),
            ('uatkeys', {'tag': 'U', 'join': ', '}),
            ('keywords', {'tag': 'K', 'join': ', '}),
            ('subjectcategory', {'tag': 'Q', 'join': '; '}),
            ('database', {'tag': 'W', 'join': '; '}),
            ('page', {'tag': 'P'}),
            ('abstract', {'tag': 'B'}),
            ('properties', {'tag': 'I', 'join': '; '}),
            ('references', {'tag': 'Z', 'join': "\n   "}),])
        pass

    def _format_affil_field(self, affils):
        formatted_affils = []
        if affils:
            for i in range(len(affils)):
                if affils[i]:
                    f = "%s(%s)" % (self.AFF_LABEL[i], affils[i])
                    formatted_affils.append(f)
        return formatted_affils

    def output(self, record):
        output_text = []
        for k, v in self.FIELD_DICT.items():
            rec_field = record.get(k, None)
            if k == "affiliations" or k == "native_authors":
                rec_field = self._format_affil_field(rec_field)
            if rec_field:
               tag = v.get("tag", None)
               join_str = v.get("join", "")
               if isinstance(rec_field, list):
                   rec_field = join_str.join(item for item in rec_field if item)
               elif isinstance(rec_field, dict):
                   rec_field = join_str.join(
                       ["%s: %s" % (fk, fv) for fk, fv in rec_field.items()])
               line_out = "%s%s %s\n" % ("%", tag, self._clean_string(rec_field))
               output_text.append(line_out)
        output = "".join(output_text)
        return output

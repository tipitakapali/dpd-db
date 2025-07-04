from db.models import DpdRoot, Lookup
from tools.configger import config_test
from tools.date_and_time import year_month_day_dash
from tools.degree_of_completion import degree_of_completion
from tools.meaning_construction import (
    make_grammar_line,
    make_meaning_combo_html,
    summarize_construction,
)


class HeadwordData:
    def __init__(self, i, fc, fi, fs):
        self.meaning = make_meaning_combo_html(i)
        self.summary = summarize_construction(i)
        self.complete = degree_of_completion(i)
        self.grammar = make_grammar_line(i)
        self.i = self.convert_newlines(i)
        self.fc = fc
        self.fi = fi
        self.fs = fs
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
        if config_test("dictionary", "make_link", "yes"):
            self.make_link = True
        else:
            self.make_link = False

    @staticmethod
    def convert_newlines(obj):
        # Convert all string attributes before session closes
        for attr_name in dir(obj):
            if (
                not attr_name.startswith("_")
                and "html" not in attr_name
                and "data" not in attr_name
            ):
                attr_value = getattr(obj, attr_name)
                if isinstance(attr_value, str):
                    try:
                        setattr(obj, attr_name, attr_value.replace("\n", "<br>"))
                    except AttributeError:
                        continue
        return obj


class RootsData:
    def __init__(self, r, frs, roots_count_dict) -> None:
        self.r: DpdRoot = r
        self.frs = frs
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()
        self.count = roots_count_dict[self.r.root]


class DeconstructorData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.deconstructions = result.deconstructor_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class VariantData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.variants = result.variants_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class SpellingData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.spellings = result.spelling_unpack
        self.app_name = "dpdict.net"
        self.date = year_month_day_dash()


class GrammarData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.grammar = result.grammar_unpack


class HelpData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.help = result.help_unpack


class AbbreviationsData:
    def __init__(self, result: Lookup):
        data = result.abbrev_unpack
        self.headword = result.lookup_key
        self.meaning = data["meaning"]
        self.pali = data["pāli"]
        self.example = data["example"]
        self.explanation = data["explanation"]


class EpdData:
    def __init__(self, result: Lookup):
        self.headword = result.lookup_key
        self.epd = result.epd_unpack

#!/usr/bin/env python3

"""
Add to the deconstructor output from
https://github.com/digitalpalidictionary/deconstructor_output.git
to the lookup database.

Used for the GitHub action which cannot currently handle the deconstructor program.
"""


import json
from db.db_helpers import get_db_session
from db.models import Lookup

from tools.lookup_is_another_value import is_another_value
from tools.paths import ProjectPaths
from tools.printer import p_green, p_title, p_yes
from tools.tic_toc import tic, toc
from tools.update_test_add import update_test_add


def main():
    
    tic()
    p_title("adding deconstructor output to lookup db")
    
    p_green("setting up data")
    pth = ProjectPaths()
    db_session = get_db_session(pth.dpd_db_path)
    lookup_db: list[Lookup] = db_session.query(Lookup).all()
    
    # top_five_dict contains the top five most likely splits
    # from the deconstruction process 
    with open(pth.deconstructor_output_repo) as f:
        top_five_dict = json.load(f)
    
    p_yes("ok")

    update_set, test_set, add_set = update_test_add(lookup_db, top_five_dict)

    p_green("updating db")

    # update test add
    update_count = 0
    for i in lookup_db:
        if i.lookup_key in update_set:
            i.deconstructor_pack(top_five_dict[i.lookup_key])
            update_count += 1
        elif i.lookup_key in test_set:
            if is_another_value(i, "deconstructor"):
                i.deconstructor = ""
                update_count += 1
            else:
                db_session.delete(i)
                update_count += 1 
    db_session.commit()
    p_yes(update_count)

    # add
    p_green("adding to db")
    add_to_db = []
    for constructed, deconstructed in top_five_dict.items():
        if constructed in add_set:
            add_me = Lookup()
            add_me.lookup_key = constructed
            add_me.deconstructor_pack(deconstructed)
            add_to_db.append(add_me)

    db_session.add_all(add_to_db)
    p_yes(len(add_to_db))

    db_session.commit()
    db_session.close()

    toc()


if __name__ == "__main__":
    main()

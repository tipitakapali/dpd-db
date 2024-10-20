#!/usr/bin/env python3

"""filtering words from db and print them"""



from db.db_helpers import get_db_session
from db.models import DpdHeadword, Russian, SBS
from tools.paths import ProjectPaths
from dps.tools.paths_dps import DPSPaths    

from sqlalchemy import and_, or_, null, not_


pth = ProjectPaths()
dpspth = DPSPaths()
db_session = get_db_session(pth.dpd_db_path)


def filtering_words():

    commentary_list = [
            "VINa", "VINt", "DNa", "MNa", "SNa", "SNt", "ANa", 
            "KHPa", "KPa", "DHPa", "UDa", "ITIa", "SNPa", "VVa", "VVt",
            "PVa", "THa", "THIa", "APAa", "APIa", "BVa", "CPa", "JAa",
            "NIDD1", "NIDD2", "PMa", "NPa", "NPt", "PTP",
            "DSa", "PPa", "VIBHa", "VIBHt", "ADHa", "ADHt",
            "KVa", "VMVt", "VSa", "PYt", "SDt", "SPV", "VAt", "VBt",
            "VISM", "VISMa",
            "PRS", "SDM", "SPM",
            "bālāvatāra", "kaccāyana", "saddanīti", "padarūpasiddhi",
            "buddhavandana", "Thai", "Sri Lanka", "Trad", "PAT PK", "MJG"
            ]

    conditions = [DpdHeadword.source_1.like(f"%{comment}%") for comment in commentary_list]
    combined_condition = or_(*conditions)

    row_count =  0

    #! for filling those which does not have Russian table and fill the conditions

    # db = db_session.query(DpdHeadword).outerjoin(
    # Russian, DpdHeadword.id == Russian.id
    #     ).filter(
    #         and_(
    #             DpdHeadword.meaning_1 != '',
    #             DpdHeadword.example_1 != '',
    #             ~combined_condition,
    #             # Russian.ru_meaning  == '',
    #             or_(
    #                 Russian.ru_meaning  == '',
    #                 # Russian.ru_meaning_raw.is_(None),
    #                 Russian.id.is_(null())
    #             )

    #         )
    #     ).all()

    #! for filling DHP in db but not in SBS and not comm words

    db = db_session.query(DpdHeadword).outerjoin(
    SBS, DpdHeadword.id == SBS.id
        ).filter(
            and_(
                or_(
                    DpdHeadword.source_1.like('%DHP%'),
                    DpdHeadword.source_2.like('%DHP%')
                ),
                not_(
                    or_(
                        SBS.sbs_source_1.like('%DHP%'),
                        SBS.sbs_source_2.like('%DHP%'),
                        SBS.sbs_source_3.like('%DHP%'),
                        SBS.sbs_source_4.like('%DHP%')
                    )
                ),
                not_(
                    or_(
                        DpdHeadword.source_1.like('%DHPa%'),
                        DpdHeadword.source_2.like('%DHPa%'),
                    )
                ),
            )
        ).all()

    #! for filling those which have lower model of gpt:

    # Call the new function to read IDs from the TSV file to exclude
    # exclude_ids = read_exclude_ids_from_tsv(f"{dpspth.ai_translated_dir}/{hight_model}.tsv")

    # # Add the conditions to the query
    # db = db_session.query(DpdHeadword).outerjoin(
    #     Russian, DpdHeadword.id == Russian.id
    #     ).filter(
    #         and_(
    #             DpdHeadword.meaning_1 != '',
    #             Russian.ru_meaning_raw != '',
    #             # func.length(Russian.ru_meaning_raw) > 20,
    #             Russian.ru_meaning == '',
    #             ~DpdHeadword.id.in_(exclude_ids)
    #         )
    #     ).order_by(DpdHeadword.ebt_count.desc()).limit(10000).all()

    # Print the db
    print("Details of filtered words")
    for word in db:
        print(f"{word.id}, {word.lemma_1}, {word.ebt_count}")
        row_count +=  1

    print(f"Total rows that fit the filter criteria: {row_count}")




def filter_and_save_txt():
    # filtering words with sbs_category and comp
    db = db_session.query(DpdHeadword).outerjoin(
    SBS, DpdHeadword.id == SBS.id
        ).filter(
            SBS.sbs_category != "",
            DpdHeadword.compound_type != "",
            DpdHeadword.grammar.like('%, comp%'),
        ).all()

    # Print the db
    row_count =  0
    print("Details of filtered words")
    for word in db:
        print(f"{word.id}, {word.lemma_1}, {word.ebt_count}")
        row_count +=  1

    print(f"Total rows that fit the filter criteria: {row_count}")

    # make a list of all constructions
    constructions = []
    for word in db:
        constructions.append(word.construction)

    original_constructions = constructions

    # remove all symbols "+" from construction
    constructions = [construction.replace("+", "") for construction in constructions]
    constructions = [construction.replace("na > a", "") for construction in constructions]
    constructions = [construction.replace(">", "") for construction in constructions]
    constructions = [construction.replace("[", "") for construction in constructions]
    constructions = [construction.replace("]", "") for construction in constructions]

    # join all constructions into one line
    constructions_str = " ".join(constructions)

    # save constructions to temp.txt
    with open(f"{pth.temp_dir}/temp.txt", "w") as file:
        file.write(constructions_str)

    # # save constructions to temp.txt
    # with open(f"{pth.temp_dir}/temp.txt", "w") as file:
    #     for construction in constructions:
    #         file.write(f"{construction}\n")

    # save constructions to temp.tsv
    with open(f"{pth.temp_dir}/temp.tsv", "w") as file:
        for original_construction in original_constructions:
            file.write(f"{original_construction}\n")

    print("filtered constructions saved to temp_dir")


if __name__ == "__main__":

    print("filtering words for some conditions")

    # filtering_words()
    filter_and_save_txt()


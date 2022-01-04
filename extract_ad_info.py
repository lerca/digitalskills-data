"""
Extracts ad information(id, title, description, date) from raw data into ad json.
"""
import json

def get_raw_data():
    """ Gets raw data as list from files """
    years = ["2008"]#["2020", "2021"] #["2006","2007","2008", "2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021"]
    data_list = []
    for year in years:
      with open(f"data/{year}.json", "r") as fd:
          data = json.load(fd)
          data.append(year) # To be able to check year for data.
          data_list.append(data)
    return data_list

def extract_fields(ads_data):
    """ Extract relevant fields from list of ads data """
    documents_input = []

    # Relevant occupation groups.
    it_concept_ids = ["UXKZ_3zZ_ipB", "DJh5_yyF_hEM", "Q5DF_juj_8do", "D9SL_mtn_vGM", "cBBa_ngH_fCx", "BAeH_eg8_  T2d", "UxT1_tPF_Kbg", "MYAz_x9m_2LJ", "VCpu_5EN_bBt", "Fv7d_YhP_YmS"]

    for ad in ads_data:
        if ad["occupation_group"]["concept_id"] in it_concept_ids:
            if(ad["description"]["text"]):
              documents_input.append({
                  "date": ad["publication_date"],
                  "doc_id": ad["id"],
                  "doc_headline": ad["headline"].lower(),
                  "doc_text": ad["description"]["text"].replace("\n\n", "").replace("\n", " ").lower()
              })

    return documents_input

def extract_ad_info():
    """ Extracts ad information from raw data """
    all_ads_data = get_raw_data()
    all_ads_info = []

    for ads_data in all_ads_data:
        year = ads_data.pop()
        documents_input = extract_fields(ads_data)

        all_ads_info.append(documents_input)

        with open(f"ads/{year}.json", "w", encoding="utf-8") as f:
              json.dump(documents_input, f, ensure_ascii=False, indent=4)

    return all_ads_info

if __name__ == "__main__":
    extract_ad_info()
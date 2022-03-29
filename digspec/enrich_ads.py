import json
import os
import requests
import pandas as pd
import numpy as np
from static_data import CITYS, BLACKLIST

PREDICTION_THRESHOLD=0.6

def get_ads_data():
    """ Gets ads data """
    years = ["2006","2007", "2008", "2009","2010","2011","2012","2013","2014","2015","2016","2017","2018","2019","2020","2021"]
    ads = []
    for year in years:
        ad = json.load(open(f"./ads/{year}.json", "r"))
        ads.extend(ad)
    return ads

def save_data_to_json(enriched_data, name="jobs"):
    data_json = enriched_data.copy()
    for key in enriched_data.keys():
        data_json[key]["series"] = enriched_data[key]["series"].to_json(indent=4)

    with open(f"enriched/enriched-{name}.json", "w", encoding="utf-8") as fd:
        json.dump(data_json, fd, ensure_ascii=False, indent=4)

def enrich_ads(documents_input, enrich_skills=False):
    JOBTECH_API_KEY = os.environ.get("JOBTECH_API_KEY")
    if not JOBTECH_API_KEY:
        JOBTECH_API_KEY = ""

    occupations = {}
    skills = {}

    print(f"> Running Enrichment API on ads data")
    try:
        headers = {
            "api-key": JOBTECH_API_KEY,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        i = 0
        adId = 0
        while len(documents_input) >= 100:
            i+=1
            body = json.dumps({
                "documents_input": documents_input[:100],
                "include_terms_info": False,
                "include_sentences": False,
                "sort_by_prediction_score": "NOT_SORTED"
            })
            req =  requests.post("https://jobad-enrichments-api.jobtechdev.se/enrichtextdocuments", data=body, headers=headers)
            resp = req.json()

            num = 5844 # TODO: Change from hardcoded num -> dynamic value
            complete_date = pd.to_datetime("1st of January, 2006") + pd.to_timedelta(np.arange(num), 'D')
            index = pd.DatetimeIndex(complete_date)
            skillsIndex = pd.DatetimeIndex(complete_date)

            for idx, ad in enumerate(resp):
                try:
                    skills_found = []
                    if(enrich_skills):
                        for skill in ad["enriched_candidates"]["competencies"]:
                            skill_name = skill["concept_label"].lower().strip()
                            if skill_name not in BLACKLIST:
                                if skill["prediction"] >= PREDICTION_THRESHOLD:
                                    if skill_name not in skills:
                                        skills[skill_name] = { "series": pd.Series([0] * num, index=skillsIndex), "employers": {}, "adIds": [], "count": 1, "skills": {}, "traits": {}, "geos": {} }

                                    adObj = documents_input[:100][idx]

                                    if adObj:
                                        date = adObj["date"].split("T")[0].split(" ")[0]
                                        skills[skill_name]["series"][date] += 1

                                        if adObj["employer"] in skills[skill_name]["employers"]:
                                            skills[skill_name]["employers"][adObj["employer"]] += 1
                                        else:
                                            skills[skill_name]["employers"][adObj["employer"]] = 1


                                        skills[skill_name]["adIds"].append(adId)
                                        adId += 1

                                        for s in skills_found:
                                            if s not in BLACKLIST:
                                                if s in skills[skill_name]["skills"]:
                                                    skills[skill_name]["skills"][s] += 1
                                                else:
                                                    skills[skill_name]["skills"][s] = 1

                                        skills_found.append(skill_name);

                                        for trait in ad["enriched_candidates"]["traits"]:
                                            trait_name= trait["concept_label"].lower().strip()
                                            if trait_name in skills[skill_name]["traits"]:
                                                skills[skill_name]["traits"][trait_name] += 1
                                            else:
                                                skills[skill_name]["traits"][trait_name] = 1

                                        for geo in ad["enriched_candidates"]["geos"]:
                                            geo_name = geo["concept_label"].lower().strip()

                                            if geo_name in skills[skill_name]["geos"]:
                                                skills[skill_name]["geos"][geo_name]["num"] += 1;
                                                if adObj["employer"] in skills[skill_name]["geos"][geo_name]["details"]:
                                                    skills[skill_name]["geos"][geo_name]["details"][adObj["employer"]] += 1
                                                else:
                                                    skills[skill_name]["geos"][geo_name]["organisations_num"] += 1;
                                                    skills[skill_name]["geos"][geo_name]["details"][adObj["employer"]] = 1
                                            else:
                                                if(geo_name in CITYS):
                                                    skills[skill_name]["geos"][geo_name] = {
                                                        "num": 1,
                                                        "organisations_num": 1,
                                                        "details": {}
                                                    }
                                                    if adObj["employer"] in skills[skill_name]["geos"][geo_name]["details"]:
                                                        skills[skill_name]["geos"][geo_name]["details"][adObj["employer"]] += 1
                                                    else:
                                                        skills[skill_name]["geos"][geo_name]["details"][adObj["employer"]] = 1
                                                        skills[skill_name]["geos"][geo_name]["organisations_num"] += 1;

                    occupations_found = []
                    for occupation in ad["enriched_candidates"]["occupations"]:
                        occupation_name = occupation["concept_label"].lower().strip()
                        if occupation_name not in BLACKLIST:
                            if occupation["prediction"] >= PREDICTION_THRESHOLD:
                                if occupation_name not in occupations:
                                    occupations[occupation_name] = { "series": pd.Series([0] * num, index=index), "employers": {} }

                                adObj = documents_input[:100][idx]

                                if adObj:
                                    date = adObj["date"].split("T")[0].split(" ")[0]
                                    occupations[occupation_name]["series"][date] += 1

                                    if adObj["employer"] in occupations[occupation_name]["employers"]:
                                        occupations[occupation_name]["employers"][adObj["employer"]] += 1
                                    else:
                                        occupations[occupation_name]["employers"][adObj["employer"]] = 1


                                    if "adIds" not in occupations[occupation_name]:
                                        occupations[occupation_name]["adIds"] = [adId]
                                    else:
                                        occupations[occupation_name]["adIds"].append(adId)
                                    adId += 1

                                    if "count" in occupations[occupation_name]:
                                        occupations[occupation_name]["count"] += 1
                                    else:
                                        occupations[occupation_name]["count"] = 1

                                    for occ in occupations_found:
                                        if occ not in BLACKLIST:
                                            if "jobs" not in occupations[occupation_name]:
                                                occupations[occupation_name]["jobs"] = {}

                                            if occ in occupations[occupation_name]["jobs"]:
                                                occupations[occupation_name]["jobs"][occ] += 1
                                            else:
                                                occupations[occupation_name]["jobs"][occ] = 1

                                    for s in skills_found:
                                        if s not in BLACKLIST:
                                            if "skills" not in occupations[occupation_name]:
                                                occupations[occupation_name]["skills"] = {}

                                            if s in occupations[occupation_name]["skills"]:
                                                occupations[occupation_name]["skills"][s] += 1
                                            else:
                                                occupations[occupation_name]["skills"][s] = 1


                                    occupations_found.append(occupation_name);

                                    for trait in ad["enriched_candidates"]["traits"]:
                                        trait_name= trait["concept_label"].lower().strip()
                                        if "traits" not in occupations[occupation_name]:
                                            occupations[occupation_name]["traits"] = {}

                                        if trait_name in occupations[occupation_name]["traits"]:
                                            occupations[occupation_name]["traits"][trait_name] += 1
                                        else:
                                            occupations[occupation_name]["traits"][trait_name] = 1

                                    for geo in ad["enriched_candidates"]["geos"]:
                                        geo_name = geo["concept_label"].lower().strip()
                                        if "geos" not in occupations[occupation_name]:
                                            occupations[occupation_name]["geos"] = {}

                                        if geo_name in occupations[occupation_name]["geos"]:
                                            occupations[occupation_name]["geos"][geo_name]["num"] += 1;
                                            if adObj["employer"] in occupations[occupation_name]["geos"][geo_name]["details"]:
                                                occupations[occupation_name]["geos"][geo_name]["details"][adObj["employer"]] += 1
                                            else:
                                                occupations[occupation_name]["geos"][geo_name]["details"][adObj["employer"]] = 1
                                                occupations[occupation_name]["geos"][geo_name]["organisations_num"] += 1
                                        else:
                                            if geo_name in CITYS:
                                                occupations[occupation_name]["geos"][geo_name] = {
                                                    "num": 1,
                                                    "organisations_num": 0,
                                                    "details": {}
                                                }
                                                if adObj["employer"] in occupations[occupation_name]["geos"][geo_name]["details"]:
                                                    occupations[occupation_name]["geos"][geo_name]["details"][adObj["employer"]] += 1
                                                else:
                                                    occupations[occupation_name]["geos"][geo_name]["details"][adObj["employer"]] = 1
                                                    occupations[occupation_name]["geos"][geo_name]["organisations_num"] += 1


                                    for skill_name in skills_found:
                                        if skill_name not in BLACKLIST:
                                            for occ in occupations_found:
                                                if "jobs" not in skills[skill_name]:
                                                   skills[skill_name]["jobs"] = {}

                                                if occ not in BLACKLIST:
                                                    if occ in skills[skill_name]["jobs"]:
                                                       skills[skill_name]["jobs"][occ] += 1
                                                    else:
                                                       skills[skill_name]["jobs"][occ] = 1

                except Exception as err:
                    print(err)

            documents_input = documents_input[100:]

        save_data_to_json(occupations)
        save_data_to_json(skills, "skills")
        if(enrich_skills):
            return skills, occupations
        else:
            return occupations
    except:
        save_data_to_json(occupations)
        save_data_to_json(skills, "skills")
        if(enrich_skills):
            return skills, occupations
        else:
            return occupations

if __name__ == "__main__":
    documents_input = list(map(lambda x: {"doc_id": str(x["doc_id"]), "date": x["date"], "doc_headline": x["doc_headline"], "doc_text": x["doc_text"]}, get_ads_data()))
    enrich_ads(documents_input, enrich_skills=True)

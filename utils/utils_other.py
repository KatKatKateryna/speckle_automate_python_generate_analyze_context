
from copy import copy
from typing import List

RESULT_BRANCH = "automate"
COLOR_ROAD = (255<<24) + (50<<16) + (50<<8) + 50 # argb
COLOR_BLD = (255<<24) + (230<<16) + (230<<8) + 230 # argb

def cleanString(text: str) -> str:
    symbols = r"/[^\d.-]/g, ''"
    new_text = text
    for s in symbols:
        new_text = new_text.split(s)[0]#.replace(s, "")
    return new_text

def fillList(vals: list, lsts: list) -> List[list]:
    if len(vals)>1: 
        lsts.append([])
    else: return

    for i, v in enumerate(vals):
        if v not in lsts[len(lsts)-1]: lsts[len(lsts)-1].append(v)
        else: 
            if len(lsts[len(lsts)-1])<=1: lsts.pop(len(lsts)-1)
            vals = copy(vals[i-1:])
            fillList(vals, lsts)
    return lsts 
    
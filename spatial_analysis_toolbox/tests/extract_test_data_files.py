#!/usr/bin/env python3

import sys
import os
import re

import pandas as pd

args = sys.argv
if len(args) <= 1:
    exit()

input_files = args[1:len(args)]
for filename in input_files:
    df = pd.read_csv(filename)
    fovs = sorted(set(df['Image Location']))
    selected = []
    count0 = 0
    for fov in fovs:
        count0 += 1
        if count0 > 2:
            break
        df2 = df.loc[df['Image Location'] == fov]
        count = 0
        for i, row in df2.iterrows():
            if count > 50:
                if row['Dye 2 Positive'] == 1:
                    count +=1
                    selected.append(row)
            else:
                selected.append(row)
                count += 1

            if count == 100:
                break
    subdf = pd.DataFrame(selected)
    nospaces = re.sub(' ', '_', filename)
    subdf.to_csv(re.sub('.csv', '_small.csv', nospaces))


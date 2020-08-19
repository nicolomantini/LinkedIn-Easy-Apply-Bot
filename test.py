# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 14:43:58 2020

@author: SRIRAM
"""
import logging
import pandas as pd
from datetime import datetime, timedelta

log = logging.getLogger(__name__)
def get_appliedIDs(filename):
    try:
        df = pd.read_csv(filename,
        header=None,
        names=['timestamp', 'jobID', 'job', 'company', 'attempted', 'result'],
        lineterminator='\n',
        encoding='utf-8')
        
        df['timestamp'] = pd.to_datetime(df['timestamp'], format="%Y-%m-%d %H:%M:%S.%f")
        df = df[df['timestamp'] > (datetime.now() - timedelta(days=2))]
        jobIDs = list(df.jobID)
        log.info(f"{len(jobIDs)} jobIDs found")
        return jobIDs
    except Exception as e:
        log.info(str(e) + " : jobIDs could not be loaded from CSV {}".format(filename))
        return None

filename='D:/Coding/Python/LinkedIn-Easy-Apply-Bot-master/output.csv'
idsList=get_appliedIDs(filename)
read_input=int(input(prompt='Enter Integer..\n'))

print(idsList)
if read_input in idsList:
    print('Yes')
else:
    print('No')
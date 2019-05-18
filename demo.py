from __future__ import unicode_literals, division

from src import index

import csv
import re

import os
import psutil
process = psutil.Process(os.getpid())
print(process.memory_info().rss / float(1000000))

films = []
with open('../tf-py-df-data/data/movies_metadata.csv') as f:
    reader = csv.reader(f)
    next(reader)
    for row in reader:
        #import ipdb; ipdb.set_trace()
        year = -1
        if len(row) >= 15 and row[14] and row[14][:4]:
            year = int(row[14][:4])
        if len(row) >= 11 and row[10]:
            try:
                popularity = float(row[10])
            except:
                popularity = 0.0

        films.append({
            "year": year,
            "title": row[8],
            "genre": (re.findall(r'\'name\': \'(.*?)\'}', row[3]) + ["Unknown"])[0],
            "language": row[7],
            "plot": row[9],
            "popularity": popularity,
        })

my_index = index.Index(
    name="my_index",
    body={
        "year": "numeric",
        "title": "text",
        "plot": "text",
        "language": "keyword",
        "genre": "keyword",
        "popularity": "numeric",
    }
)


process = psutil.Process(os.getpid())
print(process.memory_info().rss / float(1000000))

for uuid, film in enumerate(films):
    my_index.index(uuid, film)
    if uuid % 5000 == 0:
        print(process.memory_info().rss / float(1000000))

films = None
import gc
gc.enable()
gc.collect()
import time
time.sleep(2)

print(process.memory_info().rss / float(1000000))

def q(q, start=0, end=2020):
    results = my_index.search({
        "MUST": [
            {"MATCH": {"plot": {"query": q}}},
            {"MATCH": {"language": {"query": "en"}}},
            {"MATCH": {"year": {"gte": start, "lte": end}}},
        ]
    })
    for i in sorted(results, key=lambda x: (-int(x[1]), -x[0]["popularity"])):
        input("...")
        print(i)

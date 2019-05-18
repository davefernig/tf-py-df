from __future__ import division

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__)))+"/..")

import pytest

from src.index import Index


def test_should_logic():

    test_index = Index(name="test", body={
        "title": "text",
        "new": "boolean",
    })

    test_docs = [
        {"title": "AA BB CC", "new": True},
        {"title": "CC DD EE", "new": False},
        {"title": "EE FF GG", "new": False},
    ]

    for uuid, doc in enumerate(test_docs):
        test_index.index(uuid, doc)

    hits = test_index.search(body={
        "SHOULD": [
            {"MATCH": {"title": {"query": "DD"}}},
            {"MATCH": {"new": {"query": False}}},
        ]
    })

    #print(hits)
    assert True

def test_must_logic():

    test_index = Index(name="test", body={
        "title": "text",
        "new": "boolean",
    })

    test_docs = [
        {"title": "AA BB CC", "new": True},
        {"title": "CC DD EE", "new": True},
        {"title": "EE FF GG", "new": False},
    ]

    for uuid, doc in enumerate(test_docs):
        test_index.index(uuid, doc)

    hits = test_index.search(body={
        "MUST": [
            {"MATCH": {"title": {"query": "EE"}}},
            {"MATCH": {"new": {"query": False}}},
        ]
    })

    #print(hits)
    assert True

def test_nested_logic():

    test_index = Index(name="test", body={
        "title": "text",
        "genre": "keyword",
        "new": "boolean",
    })

    test_docs = [
        {"title": "AA BB", "genre": "ZZ", "new": True},
        {"title": "AA BB", "genre": "ZZ", "new": False},
        {"title": "AA BB", "genre": "YY", "new": True},
        {"title": "AA BB", "genre": "YY", "new": False},
        {"title": "BB CC", "genre": "ZZ", "new": True},
        {"title": "BB CC", "genre": "ZZ", "new": False},
        {"title": "CC DD", "genre": "YY", "new": True},
        {"title": "CC DD", "genre": "YY", "new": False},
    ]

    for uuid, doc in enumerate(test_docs):
        test_index.index(uuid, doc)

    hits = test_index.search(body={
        "SHOULD": [{
            "MUST": [ # This clause will match 1 and 5
                {"MATCH": {"title": {"query": "BB"}}},
                {"MATCH": {"genre": {"query": "ZZ"}}},
                {"MATCH": {"new": {"query": False}}},
            ]}, {
            "MUST": [ # This clause will match 6
                {"MATCH": {"title": {"query": "DD"}}},
                {"MATCH": {"new": {"query": True}}},
            ]},
        ]
    })

    #print(hits)
    assert True

def test_es_benchmark():

    test_index = Index(name="test", body={
        "content": "text",
    })

    corpus = [
        "the cat is hungry",
        "the dog is the hunter",
        "the hungry cat",
    ]

    for uuid, document in enumerate(corpus):
        test_index.index(uuid, {"content": document})

    hits = test_index.search(body={"MATCH": {"content": {"query": "the cat is hungry"}}})
    print(hits)

from __future__ import division

from nltk.stem.porter import PorterStemmer
from collections import defaultdict
from collections import Counter
import statistics
import math
import re


def apply_boost(scores, boost=1.0):
    return {uuid: score * boost for uuid, score in scores.items()}

class TagsField(object):

    def __init__(self, name):
        self.name = name
        self.mapping = {}

    def update(self, uuid, tags):
        for tag in tags:
            if tag in self.mapping:
                self.mapping[tag][uuid] = 1
            else:
                self.mapping[tag] = {uuid: 1}

    def delete(self, uuid, tags):
        for tag in tags:
            if tag in self.mapping:
                self.mapping[tag].pop(uuid)
                if not self.mapping[tag]:
                    self.mapping.pop(tag)

    def score(self, tag):
        boost = body["boost"] if "boost" in body else 1.0
        scores = self.mapping[tag] if tag in self.mapping else {}
        return apply_boost(scores, boost)

class KeywordField(object):

    def __init__(self, name):
        self.name = name
        self.mapping = {}

    def update(self, uuid, keyword):
        if keyword in self.mapping:
            self.mapping[keyword][uuid] = 1
        else:
            self.mapping[keyword] = {uuid: 1}

    def delete(self, uuid, keyword):
        if keyword in self.mapping:
            self.mapping[keyword].pop(uuid)
            if not self.mapping[keyword]:
                self.mapping.pop(keyword)

    def score(self, body):
        keyword = body["query"]
        boost = body["boost"] if "boost" in body else 1.0
        scores = self.mapping[keyword] if keyword in self.mapping else {}
        return apply_boost(scores, boost)

class TextField(object):

    def __init__(self, name, stemmer=PorterStemmer(), min_token_length=2, stopwords=set(), lowercase=True):

        # Corpus properties
        self.name = name
        self.mapping = {}
        self.corpus_size = 0
        self.avg_doc_length = 0
        self.doc_lengths = {}

        # Analysis properties
        self.min_token_length = min_token_length
        self.stopwords = stopwords
        self.lowercase = lowercase
        # TODO: Implement stemming to remove nltk dependency
        self.stemmer = stemmer

    def analyze(self, document):
        tokens = re.findall(r'[A-z0-9]+', document)
        tokens = filter(lambda t: self.min_token_length <= len(t), tokens)
        #tokens = filter(lambda t: t not in self.stopwords, tokens)
        tokens = map(lambda t: t.lower(), tokens) if self.lowercase else tokens
        #tokens = map(lambda t: self.stemmer.stem(t), tokens) if self.stemmer else tokens
        return Counter(tokens)

    def update(self, uuid, content):
        document_tokens = self.analyze(content)

        for token, count in document_tokens.items():
            if token in self.mapping:
                self.mapping[token]["num_documents"] += 1
                self.mapping[token]["documents"][uuid] = count
            else:
                self.mapping[token] = {"num_documents": 1, "documents": {uuid: count}}

        num_tokens = sum(document_tokens.values())
        self.avg_doc_length = (num_tokens + (self.corpus_size * self.avg_doc_length)) / (self.corpus_size + 1)
        self.corpus_size += 1
        self.doc_lengths[uuid] = num_tokens

    def delete(self, uuid, content):
        document_tokens = self.analyze(content)
        for token, count in document_tokens.items():
            if token in self.mapping:
                self.mapping[token]["num_documents"] -= 1
                self.mapping[token]["documents"].pop(uuid)
                if not self.mapping[token]["documents"]:
                    self.mapping.pop(token)

        self.avg_doc_length = ((self.corpus_size * self.avg_doc_length) - len(document_tokens)) / (self.corpus_size - 1)
        self.corpus_size -= 1
        self.doc_lengths.pop(uuid)

    def score(self, body, k=1.2, b=0.75):
        query = body["query"]
        boost = body["boost"] if "boost" in body else 1.0
        query_tokens = self.analyze(query)
        scores = defaultdict(float)
        for token, count in query_tokens.items():
            if token in self.mapping:
                docs_containing_q = len(self.mapping[token]["documents"])
                idf_numerator = (self.corpus_size - docs_containing_q + 0.5)
                idf_denominator = (docs_containing_q + 0.5)
                idf = math.log(1.0 + (idf_numerator / idf_denominator))
                for document, frequency_td in self.mapping[token]["documents"].items():
                    D = self.doc_lengths[document]
                    bm_numerator = (frequency_td * (k + 1.0))
                    bm_denominator = (frequency_td + k * (1 - b + b * (D / self.avg_doc_length)))
                    bm = bm_numerator / bm_denominator
                    scores[document] += idf * bm

        return apply_boost(scores, boost)

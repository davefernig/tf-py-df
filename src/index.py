from __future__ import division

from collections import defaultdict
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))

from fields import KeywordField
from fields import TextField
from fields import TagsField
import re


class Index(object):

    INDEXED_FIELD_TYPES = {
        "keyword": KeywordField,
        "text": TextField,
        "tags": TagsField,
    }

    def __init__(self, name, body):
        self.name = name
        self.mapping = body
        self.corpus_size = 0
        self.documents = {}
        self.fields = {}
        for field, field_type in body.items():
            if field_type in self.INDEXED_FIELD_TYPES:
                self.fields[field] = self.INDEXED_FIELD_TYPES[field_type](name=field)

    def index(self, uuid, document):
        self.documents[uuid] = document
        self.corpus_size += 1
        for field, content in document.items():
            if self.mapping[field] in self.INDEXED_FIELD_TYPES:
                self.fields[field].update(uuid, content)

    def delete(self, uuid):
        document = self.documents.pop(uuid)
        for field, content in document.items():
            self.fields[field].delete(uuid, content)
        self.corpus_size -= 1

    def score_numeric(self, field, body):
        boost = body["boost"] if "boost" in body else 1.0

        def __condition(x):
            if "eq" in body:
                return x == body["eq"]
            if "lt" in body and x >= body["lt"]:
                return False
            if "lte" in body and x > body["lte"]:
                return False
            if "gt" in body and x <= body["gt"]:
                return False
            if "gte" in body and x < body["gte"]:
                return False
            return True

        hits = {}
        for uuid, content in self.documents.items():
            if __condition(content[field]):
                hits[uuid] = 1 * boost

        return hits

    def score_boolean(self, field, body):
        boost = body["boost"] if "boost" in body else 1.0
        val =  body["query"]

        hits = {}
        for uuid, content in self.documents.items():
            if content[field] == val:
                hits[uuid] = 1 * boost

        return hits

    def search(self, body):
        matches = self.__search(body)
        return [(self.documents[uuid], score) for uuid, score in matches.items()]

    def __search(self, body):
        """Recursively search for documents that satisfy the
        logical clauses specified in the body.

        Parameters
        ----------
        body : dict

            One of MUST, SHOULD, MATCH

            MUST: Logical AND. Returns documents that satisfy
                  all of the specified conditions. Scores are
                  summed over all clauses by default.

            SHOULD: Logical OR. Returns documents that satisfy
                    any of the specified conditions. Scores
                    are summed over all clauses by default.

            MATCH: A field level query. Specifies a field, a
                   query value, and any optional parameters
                   accepted by the type of the field.

        Returns
        -------
        hits : dict[int: float]
            Results that satisfy the top-level query spec

        """

        if type(body) != dict or len(body) != 1:
            raise TypeError("Invalid query format")

        operator, content = body.popitem()

        if operator == "MUST":
            total_matches = {}
            partial_matches = list(map(self.__search, content))
            for result_set in partial_matches:
                for match, score in result_set.items():
                    if match not in total_matches:
                        total_matches[match] = {"count": 1, "score": score}
                    else:
                        total_matches[match]["count"] += 1
                        total_matches[match]["score"] += score

            result = {}
            for hit, data in total_matches.items():
                if data["count"] == len(partial_matches):
                    result[hit] = data["score"]

            return result

        if operator == "SHOULD":
            total_matches = defaultdict(int)
            partial_matches = map(self.__search, content)
            for result_set in partial_matches:
                for match, score in result_set.items():
                    total_matches[match] += score
            return total_matches

        if operator == "MATCH":
            field, body = content.popitem()
            field_type = self.mapping[field]

            if field_type in self.INDEXED_FIELD_TYPES:
                return self.fields[field].score(body)

            if field_type == "boolean":
                return self.score_boolean(field, body)

            if field_type == "numeric":
                return self.score_numeric(field, body)

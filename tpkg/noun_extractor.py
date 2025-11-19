# tpkg/noun_extractor.py

import spacy

# Lazy-loaded model (loaded on first call only)
_nlp = None

# Common nouns too generic to be useful in graph
STOP_NOUNS = {
    "thing", "something", "anything", "everything",
    "way", "time", "part", "one", "someone",
    "person", "people", "area"
}


def _get_nlp():
    """
    Loads the SpaCy model only once.
    Saves ~500ms per import and prevents race conditions.
    """
    global _nlp
    if _nlp is None:
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


def extract_nouns(text):
    """
    Extracts clean lemmatized nouns from text by:
      - Running text through SpaCy's pipeline
      - Selecting tokens with POS = NOUN or PROPN
      - Converting to lowercase lemma (canonical form)
      - Removing stop nouns and very short tokens
    """

    doc = _get_nlp()(text)  # runs SpaCy pipeline → tokenizes + POS tags
    nouns = set()

    for token in doc:
        # only real nouns → SpaCy POS tagger determines this from sentence structure
        if token.pos_ in ("NOUN", "PROPN"):
            lemma = token.lemma_.lower()

            # skip useless nouns & extremely short tokens
            if len(lemma) < 3: 
                continue
            if lemma in STOP_NOUNS:
                continue

            nouns.add(lemma)

    return list(nouns)

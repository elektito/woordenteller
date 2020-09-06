from frog import Frog, FrogOptions


frog = Frog(FrogOptions(chunking=False,
                        parser=False))

def get_words(s):
    result = frog.process(s)

    kept, thrown = set(), set()
    for word in result:
        if all(not c.isalpha() for c in word['lemma']):
            thrown.add(word['lemma'])
        elif word['ner'] == 'O':
            kept.add(word['lemma'])
        else:
            thrown.add(word['lemma'])

    return kept, thrown

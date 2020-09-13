from frog import Frog, FrogOptions


frog = Frog(FrogOptions(chunking=False,
                        parser=False))

def get_words(s, debug=False):
    result = frog.process(s)

    kept, thrown = set(), set()
    for word in result:
        if all(not c.isalpha() for c in word['lemma']):
            thrown.add(word['lemma'])
        elif word['ner'] == 'O':
            kept.add(word['lemma'])
        else:
            to_add = word['lemma']
            if debug:
                to_add += f' ({word["ner"]})'
            thrown.add(to_add)

    return kept, thrown

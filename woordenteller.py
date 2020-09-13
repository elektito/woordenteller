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
            if '_' in word['ner']:
                # sometimes phrases are returned instead of words,
                # e.g. "zeg maar" will be returned as "zeggen_maar"
                # with the NER value being "O_O", so two types are
                # actually returned separated by an underscore. We
                # split these phrases again and add the "O" types to
                # the "kept" list.
                words = word['lemma'].split('_')
                types = word['ner'].split('_')
                if 'O' in types:
                    for w, t in zip(words, types):
                        if t == 'O':
                            kept.add(w)
                        else:
                            thrown.add(_format_thrown_word(w, t, debug))
                else:
                    thrown.add(_format_thrown_word(
                        word['lemma'], word['ner'], debug))
            else:
                thrown.add(_format_thrown_word(
                    word['lemma'], word['ner'], debug))

    return kept, thrown


def _format_thrown_word(word, ner, debug):
    result = word
    if debug:
        result += f' ({ner})'
    return result

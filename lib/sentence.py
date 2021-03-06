# -*- coding: utf-8 -*-


"""
sentence utility module
__author__ = 'krikit <krikit@naver.com>'
__copyright__ = 'No copyright, just copyleft! ;)'
"""


###########
# imports #
###########
from __future__ import unicode_literals

import gazette


#########
# types #
#########
class NE(object):
    """
    named entity
    """
    def __init__(self, json_obj):
        """
        initializer
        :param json_obj:  JSON object of NE
        """
        self.json_obj = json_obj

    def id(self):    # pylint: disable=C0103
        """
        ID
        :return:  ID
        """
        return self.json_obj['id']

    def set_id(self, identity):
        """
        set ID
        """
        self.json_obj['id'] = identity

    def text(self):
        """
        text
        :return:   text
        """
        return self.json_obj['text']

    def category(self):
        """
        category of entity
        :return:  category
        """
        return self.json_obj['type']

    def set_category(self, category):
        """
        set category
        :param  category:  category
        """
        self.json_obj['type'] = category

    def begin(self):
        """
        morpheme begin id
        :return:  morpheme begin id
        """
        return self.json_obj['begin']

    def end(self):
        """
        morpheme end id
        :return:  morpheme end id
        """
        return self.json_obj['end']


class Morp(object):
    """
    morpheme
    """
    def __init__(self, json_obj):
        """
        initializer
        :param json_obj:  JSON object of morpheme
        """
        self.json_obj = json_obj

    def to_dbg_str(self):
        """
        make string for debugging
        :return:  debug string
        """
        return '%d:%s/%s' % (self.id(), self.lemma(), self.tag())

    def id(self):    # pylint: disable=C0103
        """
        ID
        :return:  ID
        """
        return self.json_obj['id']

    def lemma(self):
        """
        lemma
        :return:  lemma
        """
        return self.json_obj['lemma']

    def tag(self):
        """
        PoS tag
        :return:  PoS tag
        """
        return self.json_obj['type']

    def lex_form(self):
        """
        get lexical form
        :return:  lexical form
        """
        form = []
        for char in self.lemma():
            if self.is_hangul(char):
                form.append('가')
            elif (ord('a') <= ord(char) <= ord('z')) or (ord('A') <= ord(char) <= ord('Z')):
                form.append('A')
            elif ord('0') <= ord(char) <= ord('9'):
                form.append('0')
            elif self.is_cjk(char):
                form.append('漢')
            else:
                form.append('.')
        return ''.join(form)

    @classmethod
    def is_hangul(cls, char):
        """
        whether character is hangul character
        :param  char:  character
        :return:       whether hangul character or not
        """
        code = ord(char)
        if 0x1100 <= code <= 0x11FF:
            return True
        elif 0xAC00 <= code <= 0xD7AF:
            return True
        return False

    @classmethod
    def is_cjk(cls, char):
        """
        whether character is CJK character
        :param  char:  character
        :return:       whether CJK character or not
        """
        code = ord(char)
        if 0x4E00 <= code <= 0x9FFF:
            return True
        return False


class Word(object):
    """
    word
    """
    def __init__(self, json_obj):
        """
        initializer
        :param json_obj:  JSON object of word
        """
        self.json_obj = json_obj

    def id(self):    # pylint: disable=C0103
        """
        ID
        :return:  ID
        """
        return self.json_obj['id']

    def begin(self):
        """
        morpheme begin id
        :return:  morpheme begin id
        """
        return self.json_obj['begin']

    def end(self):
        """
        morpheme end id
        :return:  morpheme end id
        """
        return self.json_obj['end']


class Sentence(object):    # pylint: disable=R0902
    """
    sentence
    """
    def __init__(self, json_obj):
        """
        initializer
        :param json_obj:  JSON object of sentence
        """
        self.json_obj = json_obj
        self.words = [Word(_) for _ in self.json_obj['word']]
        self.morps = [Morp(_) for _ in self.json_obj['morp']]
        self.nes = [NE(_) for _ in self.json_obj['NE']] if 'NE' in self.json_obj else []
        self.mid2wid = {}    # index of morp ID -> word ID
        self._index_mid_to_wid()
        self.mid2nid = {}    # index of morp ID -> NE ID
        self._index_mid_to_nid()
        self.dic_nes = []
        self.mid2did = {}    # index of morp ID -> gazette matched NE ID

    def to_dbg_str(self):
        """
        make string for debugging
        :return:  debug string
        """
        return '[%d] %s' % (self.id(), ' '.join([_.to_dbg_str() for _ in self.morps]))

    def id(self):    # pylint: disable=C0103
        """
        ID
        :return:  ID
        """
        return self.json_obj['id']

    @classmethod
    def _label(cls, index, nes, morp_id):
        """
        get label of given morpheme ID with index and entities
        :param  index:    morpheme ID -> entity ID index
        :param  nes:      entities
        :param  morp_id:  morpheme ID
        :return:          label
        """
        if morp_id not in index:
            return 'O'
        entity = nes[index[morp_id]]
        iob = 'B' if morp_id == entity.begin() else 'I'
        if isinstance(entity.category(), list):
            return ','.join(['%s-%s' % (iob, _) for _ in entity.category()])
        else:
            return '%s-%s' % (iob, entity.category())

    def label(self, morp_id):
        """
        get output label of given morpheme ID
        :param  morp_id:  morpheme ID
        :return:          output label
        """
        return self._label(self.mid2nid, self.nes, morp_id)

    def dic_label(self, morp_id):
        """
        get dictionary label of given morpheme ID
        :param  morp_id:  morpheme ID
        :return:          dictionary label
        """
        return self._label(self.mid2did, self.dic_nes, morp_id)

    def _index_mid_to_wid(self):
        """
        make index map from morp ID to word ID
        :param  sent:  sentence JSON object
        """
        self.mid2wid = {}
        for word in self.words:
            word_id = word.id()
            for morp_id in range(word.begin(), word.end()+1):
                self.mid2wid[morp_id] = word_id

    def _index_mid_to_nid(self):
        """
        make index map from morp ID to NE ID
        :param  sent:  sentence JSON object
        """
        self.mid2nid = {}
        for entity in self.nes:
            ne_id = entity.id()
            for morp_id in range(entity.begin(), entity.end()+1):
                self.mid2nid[morp_id] = ne_id

    def tag_nes(self, dic, max_key_len):
        """
        tag NEs in sentence with gazette
        :param  dic:          gazette dictionary
        :param  max_key_len:  maximum length of gazette keys
        """
        self.dic_nes = [NE(_) for _ in gazette.tag_nes(dic, max_key_len, self)]
        self.mid2did = {}
        for dic_ne in self.dic_nes:
            dic_ne_id = dic_ne.id()
            for morp_id in range(dic_ne.begin(), dic_ne.end()+1):
                self.mid2did[morp_id] = dic_ne_id

    def is_person(self, morp_id):
        """
        whether current morpheme is single morpheme person(PS) or not
        :param  morp_id:  morpheme ID
        :return:          person or not
        """
        if morp_id not in self.mid2nid:
            return False
        ne_id = self.mid2nid[morp_id]
        entity = self.nes[ne_id]
        if entity.category() != 'PS':
            return False
        return entity.begin() == entity.end()

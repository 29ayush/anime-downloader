import logging
import re
from anime_downloader.extractors.base_extractor import BaseExtractor
from anime_downloader.sites import helpers

logger = logging.getLogger(__name__)

def base62ToAlphaNum( number ):
    alphaNum = ""
    while number:
        r = number % 62;
        number = number//62;
        if r < 10:
            alphaNum = str( r ) + alphaNum
        elif r < 36:
            alphaNum = chr( r + 87 ) + alphaNum
        else:
            alphaNum = chr( r + 29 ) + alphaNum
    return alphaNum

def alphaNumToBase62( alphaNum ):
    base62 = 0
    for i in alphaNum:
        o = ord(i)
        if 'A' <= i <= 'Z':
            value = o - 29
        elif 'a' <= i <=' z':
            value = o - 87
        else:
            value = int(i)
        base62 = base62 * 62 + value
    return base62

class Kwik(BaseExtractor):
    '''Extracts video url from kwik pages, Kwik has some `security`
       which allows to access kwik pages when only refered by something
       and the kwik video stream when refered through the corresponding
       kwik video page.
    '''
    def _get_data(self):

        # Kwik servers don't have direct link access you need to be referred
        # from somewhere, I will just use the url itself.

        site_url = self.url.replace('kwik.cx/e/', 'kwik.cx/f/')
        download_url = self.url.replace('kwik.cx/e/', 'kwik.cx/d/')

        kwik_text = helpers.get(site_url, referer=site_url).text
        script_re = re.compile( r'eval.*\<script\>', re.DOTALL )
        script_text = script_re.search(kwik_text).group()

        source_parts_re = re.compile( r',\'([^\']*)\'\.split\(\'\|\'\)', re.DOTALL )
        source_list = source_parts_re.search( script_text ).group(1).split("|")

        tokenIndex = base62ToAlphaNum( source_list.index("_token") )
        varIndex = base62ToAlphaNum( source_list.index("var") )

        tokenVariableChar = re.search( r'%s.*?\+ ([^.]*)' % tokenIndex,
                                       script_text).group(1)

        tokenChar = re.search( r'%s %s="(.*?)"' % (varIndex, tokenVariableChar),
                               script_text).group(1)
        
        token = source_list[ alphaNumToBase62( tokenChar ) ]

        stream_url = helpers.post(post_url,
                                  referer=download_url,
                                  data={'_token': token},
                                  allow_redirects=False).headers['Location']

        title = stream_url.rsplit('/', 1)[-1].rsplit('.', 1)[0]

        logger.debug('Stream URL: %s' % stream_url)
        return {
            'stream_url': stream_url,
            'meta': {
                'title': title,
                'thumbnail': ''
            },
            'referer': None
        }

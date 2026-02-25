import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, orderedSet, traverse_obj


class KinescopeIE(InfoExtractor):
    IE_NAME = 'Kinescope'
    IE_DESC = 'kinescope.io'
    _VALID_URL = r'https?://kinescope\.io/(?!embed/)(?P<id>[A-Za-z0-9][A-Za-z0-9-]*)'

    def _real_extract(self, url):
        video_id = self._match_id(url)
        webpage = self._download_webpage(url, video_id)

        player_options = self._search_json(
            r'var\s+playerOptions\s*=\s*',
            webpage, 'player options', video_id,
        )

        item = traverse_obj(player_options, ('playlist', 0)) or {}
        uuid = item.get('id') or video_id
        title = item.get('title') or video_id

        hls_url = traverse_obj(item, ('sources', 'hls', 'src'))
        if not hls_url:
            raise ExtractorError('No HLS stream found', expected=True)

        formats, subtitles = self._extract_m3u8_formats_and_subtitles(
            hls_url, uuid, 'mp4',
        )

        for vtt in (traverse_obj(item, ('vtt', ...)) or []):
            lang = vtt.get('srcLang', 'und')
            subtitles.setdefault(lang, []).append({
                'url': vtt['src'],
                'ext': 'vtt',
                'name': vtt.get('label'),
            })

        duration = traverse_obj(item, ('meta', 'duration'))

        return {
            'id': uuid,
            'title': title,
            'formats': formats,
            'subtitles': subtitles,
            'thumbnail': traverse_obj(item, ('poster', 'src', 'src')),
            'duration': float(duration) if duration else None,
        }


class SynchronizeLectureIE(InfoExtractor):
    IE_NAME = 'synchronize:lecture'
    IE_DESC = 'synchronize.ru lecture (via Kinescope)'
    _VALID_URL = r'https?://app\.synchronize\.ru/listener/educations/(?P<ed_id>\d+)/cohorts/(?P<co_id>\d+)/plans/(?P<pl_id>\d+)/lectures/(?P<id>\d+)'

    _TESTS = [{
        'url': 'https://app.synchronize.ru/listener/educations/192/cohorts/431/plans/493/lectures/166',
        'info_dict': {
            'id': '166',
            'ext': 'mp4',
        },
        'skip': 'Requires authentication',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        video_id = mobj.group('id')

        webpage, urlh = self._download_webpage_handle(url, video_id)

        # Check for redirect to login page
        if '/session/new' in urlh.url:
            raise ExtractorError(
                'This video is only available to authenticated users. '
                'Use --cookies-from-browser chrome (or --cookies cookies.txt) to provide your session.',
                expected=True,
            )

        kinescope_url = self._search_regex(
            r'data-kinescope-url-value="([^"]+)"',
            webpage,
            'kinescope url',
        )

        title = self._html_search_regex(
            r'<h1[^>]*>\s*([^<]+?)\s*</h1>',
            webpage,
            'title',
            default=video_id,
        )

        return self.url_result(kinescope_url, ie=KinescopeIE.ie_key(), video_title=title)


class SynchronizePlanIE(InfoExtractor):
    IE_NAME = 'synchronize:plan'
    IE_DESC = 'synchronize.ru plan/course (playlist of lectures)'
    _VALID_URL = r'https?://app\.synchronize\.ru/listener/educations/(?P<ed_id>\d+)/cohorts/(?P<co_id>\d+)/plans/(?P<id>\d+)(?:/?)$'

    _TESTS = [{
        'url': 'https://app.synchronize.ru/listener/educations/192/cohorts/431/plans/493',
        'info_dict': {
            'id': '493',
            '_type': 'playlist',
        },
        'skip': 'Requires authentication',
    }]

    def _real_extract(self, url):
        mobj = self._match_valid_url(url)
        playlist_id = mobj.group('id')
        ed_id = mobj.group('ed_id')
        co_id = mobj.group('co_id')

        webpage, urlh = self._download_webpage_handle(url, playlist_id)

        # Check for redirect to login page
        if '/session/new' in urlh.url:
            raise ExtractorError(
                'This playlist is only available to authenticated users. '
                'Use --cookies-from-browser chrome (or --cookies cookies.txt) to provide your session.',
                expected=True,
            )

        # Extract playlist title from page heading
        title = self._html_search_regex(
            r'<h1[^>]*>\s*([^<]+?)\s*</h1>',
            webpage,
            'plan title',
            default=playlist_id,
        )

        lecture_href_re = (
            r'href="(/listener/educations/%s/cohorts/%s/plans/%s/lectures/\d+)"'
            % (re.escape(ed_id), re.escape(co_id), re.escape(playlist_id))
        )

        entries = []
        seen = set()

        for chapter_match in re.finditer(
            r'<section\s+id="chapter-(\d+)"[^>]*>(.*?)</section>',
            webpage, re.DOTALL,
        ):
            chapter_num = int(chapter_match.group(1))
            chapter_html = chapter_match.group(2)

            chapter_title = self._html_search_regex(
                r'<span[^>]+lg:text-h4[^>]*>\s*([^<]+?)\s*</span>',
                chapter_html,
                'chapter title',
                default='Chapter %d' % chapter_num,
            )

            for href in orderedSet(re.findall(lecture_href_re, chapter_html)):
                if href not in seen:
                    seen.add(href)
                    entries.append(self.url_result(
                        'https://app.synchronize.ru' + href,
                        ie=SynchronizeLectureIE.ie_key(),
                        chapter=chapter_title,
                        chapter_number=chapter_num,
                    ))

        if not entries:
            raise ExtractorError('No lectures found in plan %s' % playlist_id, expected=True)

        return self.playlist_result(entries, playlist_id, title)

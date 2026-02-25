import re

from yt_dlp.extractor.common import InfoExtractor
from yt_dlp.utils import ExtractorError, orderedSet


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

        return self.url_result(kinescope_url, ie='Kinescope', video_title=title)


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

        # Find all lecture hrefs in the page
        lecture_pattern = (
            r'href="(/listener/educations/%s/cohorts/%s/plans/%s/lectures/\d+)"'
            % (re.escape(ed_id), re.escape(co_id), re.escape(playlist_id))
        )
        lecture_hrefs = orderedSet(re.findall(lecture_pattern, webpage))

        if not lecture_hrefs:
            raise ExtractorError('No lectures found in plan %s' % playlist_id, expected=True)

        entries = [
            self.url_result(
                'https://app.synchronize.ru' + href,
                ie=SynchronizeLectureIE.ie_key(),
            )
            for href in lecture_hrefs
        ]

        return self.playlist_result(entries, playlist_id, title)

"""Utilities for Tarmac."""
import re


def get_review_url(proposal):
    """Return the web url for a given proposal."""
    urlp = re.compile('http[s]?://api\.(.*)launchpad\.net/[^/]+/')
    merge_url = urlp.sub(
        'http://code.launchpad.net/', proposal.self_link)
    return merge_url

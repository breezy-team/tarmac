"""Tests for the commitmessage plugin."""

from tarmac.plugins.commitmessage import (
    CommitMessageTemplate, CommitMessageTemplateInfo)
from tarmac.tests import TarmacTestCase
from tarmac.tests import Thing


class TestCommitMessageTemplateInfo(TarmacTestCase):

    def setUp(self):
        super(TestCommitMessageTemplateInfo, self).setUp()
        self.proposal = Thing(
            source_branch=Thing(
                owner=Thing(display_name="Arthur Author", name="arthur"),
                linked_bugs=[Thing(id=1234), Thing(id=5678)]),
            commit_message="Awesome",
            reviewer=Thing(display_name="Randy Reviewer"),
            votes=[
                Thing(
                    comment=Thing(vote="Approve"),
                    reviewer=Thing(
                        display_name="Virgil Voter", name="virgil")),
                Thing(
                    comment=Thing(vote="Approve"),
                    reviewer=Thing(
                        display_name="Virginia Voter", name="virginia")),
                ],
            self_link="http://api.launchpad.net/1.0/~rockstar/tarmac/tarmac/+merge/1",
            web_link='https://code.launchpad.net/~rockstar/tarmac/tarmac/+merge/1',
        )
        self.info = CommitMessageTemplateInfo(self.proposal)

    def test_author(self):
        self.assertEqual("Arthur Author", self.info.author)

    def test_author_nick(self):
        self.assertEqual("arthur", self.info.author_nick)

    def test_commit_message(self):
        self.assertEqual("Awesome", self.info.commit_message)

    def test_reviewer(self):
        self.assertEqual("Randy Reviewer", self.info.reviewer)

    def test_approved_by(self):
        self.assertEqual(
            "Virgil Voter, Virginia Voter",
            self.info.approved_by)

    def test_review_url(self):
        self.assertEqual(
            "https://code.launchpad.net/~rockstar/tarmac/tarmac/+merge/1",
            self.info.review_url)

    def test_approved_by_nicks(self):
        self.assertEqual(
            "virgil,virginia",
            self.info.approved_by_nicks)

    def test_bugs_fixed(self):
        self.assertEqual("1234,5678", self.info.bugs_fixed)

    def test___getitem__(self):
        """Subscripts can be used to look up attributes too.

        None is never returned; the empty string is substituted. Names
        beginning with _ always resolve to the empty string.
        """
        for name in dir(self.info):
            attr, item = getattr(self.info, name), self.info[name]
            self.assertTrue(item is not None, "%r is not None" % (item,))
            if name.startswith('_'):
                self.assertEqual("", item)
            else:
                self.assertEqual(attr, item)


class FakeCommitMessageTemplateInfo(object):

    def __getitem__(self, name):
        if name.startswith("_"):
            return ""
        else:
            return "{info:%s}" % name


class TestCommitMessageTemplate(TarmacTestCase):

    def test_render(self):
        message_template = CommitMessageTemplate()
        message_info = FakeCommitMessageTemplateInfo()
        render = message_template.render
        # Render without replacement.
        self.assertEqual("", render("", message_info))
        self.assertEqual("foo", render("foo", message_info))
        # Render with replacement.
        self.assertEqual(
            "{info:author}",
            render("%(author)s", message_info))
        self.assertEqual(
            "{info:author} {info:reviewer}",
            render("%(author)s %(reviewer)s", message_info))

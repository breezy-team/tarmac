"""Tests for the commitmessage plugin."""

from tarmac.plugins.commitmessage import (
    CommitMessageTemplate, CommitMessageTemplateInfo)
from tarmac.tests import TarmacTestCase


class thing(object):
    def __init__(self, **names):
        self.__dict__.update(names)


class TestCommitMessageTemplateInfo(TarmacTestCase):

    def setUp(self):
        super(TestCommitMessageTemplateInfo, self).setUp()
        self.proposal = thing(
            source_branch=thing(
                owner=thing(
                    display_name="Arthur Author")),
            commit_message="Awesome",
            reviewer=thing(
                display_name="Randy Reviewer"))
        self.info = CommitMessageTemplateInfo(self.proposal)

    def test_author(self):
        self.assertEqual("Arthur Author", self.info.author)

    def test_commit_message(self):
        self.assertEqual("Awesome", self.info.commit_message)

    def test_reviewer(self):
        self.assertEqual("Randy Reviewer", self.info.reviewer)

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
                self.assertTrue(attr is item, "%r is not %r" % (attr, item))


class FakeInfo(object):
    def __getitem__(self, name):
        if name.startswith("_"):
            return ""
        else:
            return "{info:%s}" % name


class TestCommitMessageTemplate(TarmacTestCase):

    def setUp(self):
        super(TestCommitMessageTemplate, self).setUp()
        self.template = CommitMessageTemplate()
        self.info = FakeInfo()

    def test_render(self):
        message_template = CommitMessageTemplate()
        render = message_template.render
        # Render without replacement.
        self.assertEqual("", render("", self.info))
        self.assertEqual("foo", render("foo", self.info))
        # Render with replacement.
        self.assertEqual(
            "{info:author}",
            render("%(author)s", self.info))
        self.assertEqual(
            "{info:author} {info:reviewer}",
            render("%(author)s %(reviewer)s", self.info))

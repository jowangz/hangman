#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import logging
import webapp2

from google.appengine.api import mail, app_identity
from google.appengine.ext import ndb
from api import HangmanApi
from utils import get_by_urlsafe

from models import User, Game


class SendReminderEmail(webapp2.RequestHandler):
    def get(self):
        """Send a reminder email to each User with an email who has
        games in progress. Email body includes a count of active
        games and their urlsafe keys
        Called every everyday at 9:00 AM"""
        games = Game.query(Game.game_over == False) 
        for game in games:
            user = User.query(User.key == game.user).get()
            subject = 'This is a reminder!'
            body = 'Hello {}, you have game in progress. Their' \
                   ' keys are: {}'.\
                format(user.name,
                       ''.join(game.key.urlsafe()))
            logging.debug(body)
            # This will send test emails, the arguments to send_mail are:
            # from, to, subject, body
            mail.send_mail('noreply@{}.appspotmail.com'.
                           format(app_identity.get_application_id()),
                           user.email,
                           subject,
                           body)


app = webapp2.WSGIApplication([
    ('/crons/send_reminder', SendReminderEmail),
], debug=True)

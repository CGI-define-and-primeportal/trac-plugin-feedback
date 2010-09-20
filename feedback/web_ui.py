# coding: utf-8
#
# Copyright (c) 2010, Logica
# 
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#     * Redistributions of source code must retain the above copyright 
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the <ORGANIZATION> nor the names of its
#       contributors may be used to endorse or promote products derived from
#       this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR
# PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------
# Created on 14 Sep 2010
# @author enmarkp
import re
from datetime import datetime
from genshi.builder import tag
from genshi.filters.transform import Transformer
from genshi.template.loader import TemplateLoader
from pkg_resources import resource_filename
from trac.util.datefmt import to_utimestamp, utc
from trac.config import ListOption
from trac.core import implements, Component
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.env import IEnvironmentSetupParticipant
from trac.db.schema import Table, Column
from trac.db.api import DatabaseManager
from trac.web.chrome import ITemplateProvider, add_javascript, add_stylesheet,\
    INavigationContributor, Chrome
from trac.util.translation import _


class Feedback(Component):
    realms = ListOption('feedback', 'realms', '*',
                        doc="Show feedback option in these realms")
    implements(ITemplateStreamFilter, IRequestHandler, INavigationContributor,
               IEnvironmentSetupParticipant, ITemplateProvider)
    
    _schema = [Table('project_feedback', key='id')[
                   Column('id', type='int', auto_increment=True),
                   Column('author'),
                   Column('feedback'),
                   Column('path'),
                   Column('created', type='int64'),
                   Column('modified', type='int64')]]
    
    # INavigationContributor
    
    def get_active_navigation_item(self, req):
        if (req.perm.has_permission('TRAC_ADMIN') and 
                req.path_info.startswith("/feedback")):
            return 'feedback'
        return ''

    def get_navigation_items(self, req):
        if req.perm.has_permission('TRAC_ADMIN'):
            yield ('mainnav', 'feedback', 
                   tag.a("Feedback", href=req.href.feedback()))
            
    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        if req.authname == 'anonymous':
            return stream
        add_stylesheet(req, 'feedback/feedback.css')
        add_javascript(req, 'feedback/feedback.js')
        Chrome(self.env).add_wiki_toolbars(req)
        tmpl = TemplateLoader(self.get_templates_dirs()).load('feedback-box.html')
        path = req.path_info
        if req.query_string:
            path = '%s?%s' % (path, req.query_string)
        feedbackbox = tmpl.generate(href=req.href, path=path)
        stream |= Transformer('//body').append(feedbackbox)
        return stream
    
    # IRequestHandler
    _url_re = re.compile(r'^/feedback(?:/(\d+))?/?$')
    def match_request(self, req):
        m = self._url_re.search(req.path_info)
        if m is None:
            return False
        id_ = m.group(1)
        req.args['feedback_id'] = id_ and int(id_) or None
        return True
    
    def process_request(self, req):
        feedback = []
        if req.method == 'POST':
            author = req.authname
            action = req.args.get('action', 'create')
            if action == 'create':
                feedback = req.args['feedback']
                path = req.args['path']
                created = modified = to_utimestamp(datetime.now(utc))
                @self.env.with_transaction()
                def add_feedback(db):
                    cursor = db.cursor()
                    self.log.debug('INSERT INTO project_feedback ('
                                   'author, feedback, path, created, modified'
                                   ") VALUES ('%s', '%s', '%s', '%s', '%s')", 
                                   author, feedback, path, created, modified)
                    cursor.execute('INSERT INTO project_feedback ('
                                   'author, feedback, path, created, modified'
                                   ') VALUES (%s, %s, %s, %s, %s)', 
                                   (author, feedback, path, created, modified))
                msg = _("Your feedback has been received, thank you")
            elif action == 'delete':
                id_ = req.args['feedback_id']
                @self.env.with_transaction()
                def del_feedback(db):
                    cursor = db.cursor()
                    if req.perm.has_permission('TRAC_ADMIN'):
                        cursor.execute('DELETE FROM project_feedback '
                                       'WHERE id=%s', (id_,))
                    else:
                        cursor.execute('DELETE FROM project_feedback '
                                       'WHERE id=%s AND author=%s', 
                                       (id_, author))
                msg = _("Feedback item %s was deleted") % id_
            if req.get_header('X-Requested-With') == 'XMLHttpRequest':
                req.send('{"message":"%s"}' % msg, 'text/json')
            else:
                req.redirect(req.href.feedback())
        else:
            db = self.env.get_read_db()
            cursor = db.cursor()
            if req.perm.has_permission('TRAC_ADMIN'):
                cursor.execute('SELECT * FROM project_feedback ORDER BY created DESC')
            else:
                cursor.execute('SELECT * FROM project_feedback '
                               'WHERE author=%s ORDER BY created DESC', (req.authname,))
            feedback = list(cursor)
        return 'feedback.html', dict(href=req.href, feedback=feedback), None

    # IEnvironmentSetupParticipant
    
    def environment_created(self):
        @self.env.with_transaction()
        def try_upgrade(db=None):
            self.upgrade_environment(db)

    def environment_needs_upgrade(self, db):
        try:
            @self.env.with_transaction()
            def check(db):
                sql = ('SELECT id, author, feedback, path, created, '
                       'modified FROM project_feedback LIMIT 1')
                cursor = db.cursor()
                cursor.execute(sql)
                cursor.fetchone()
        except Exception, e:
            self.log.debug("Upgrade of schema needed for feedback plugin", exc_info=True)
            return True
        else:
            return False

    def upgrade_environment(self, db):
        self.log.debug("Upgrading schema for feedback plugin")
        db_backend, _ = DatabaseManager(self.env).get_connector()
        cursor = db.cursor()
        for table in self._schema:
            for stmt in db_backend.to_sql(table):
                self.log.debug(stmt)
                cursor.execute(stmt)

   
    # ITemplateProvider
    
    def get_htdocs_dirs(self):
        return [('feedback', resource_filename(__name__, 'htdocs'))]
    
    def get_templates_dirs(self):
        return [resource_filename(__name__, 'templates')]

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
'''
Created on 14 Sep 2010

@author: enmarkp
'''
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
    INavigationContributor
from trac.util.translation import _


class Feedback(Component):
    realms = ListOption('feedback', 'realms', '*',
                        doc="Show feedback option in these realms")
    implements(ITemplateStreamFilter, IRequestHandler, INavigationContributor,
               IEnvironmentSetupParticipant, ITemplateProvider)
    
    _schema = [Table('project_feedback')[
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
        if req.authname == 'anonymous':# or filename == 'feedback.html':
            return stream
        add_stylesheet(req, 'feedback/feedback.css')
        add_javascript(req, 'feedback/feedback.js')
        tmpl = TemplateLoader(self.get_templates_dirs()).load('feedback-box.html')
        path = req.path_info
        if req.query_string:
            path = '%s?%s' % (path, req.query_string)
        feedbackbox = tmpl.generate(href=req.href, path=path)
        stream |= Transformer('//body').append(feedbackbox)
        return stream
    
    # IRequestHandler
    
    def match_request(self, req):
        return req.path_info == '/feedback'
    
    def process_request(self, req):
        feedback = []
        if req.method == 'POST':
            # might add more actions later
            if req.args.get('action', 'create') == 'create':
                author = req.authname
                feedback = req.args['feedback']
                path = req.args['path']
                created = modified = to_utimestamp(datetime.now(utc))
                @self.env.with_transaction()
                def add_feedback(db):
                    cursor = db.cursor()
                    self.log.debug('Inserting feedback from %s: %s', author, 
                                   feedback)
                    cursor.execute('INSERT INTO project_feedback VALUES '
                                   '(%s, %s, %s, %s, %s)', 
                                   (author, feedback, path, created, modified))
                if req.get_header('X-Requested-With') == 'XMLHttpRequest':
                    req.send('{"message":"%s"}' % _("Your feedback has been "
                                                  "received, thank you"), 
                                                  'text/json')
                else:
                    req.redirect(req.href.feedback())
        else:
            db = self.env.get_read_db()
            cursor = db.cursor()
            if req.perm.has_permission('TRAC_ADMIN'):
                cursor.execute('SELECT * FROM project_feedback')
            else:
                cursor.execute('SELECT * FROM project_feedback WHERE '
                               'author=%s', (req.authname,))
            feedback = list(cursor)
        return 'feedback.html', dict(href=req.href, feedback=feedback), None

    # IEnvironmentSetupParticipant
    
    def environment_created(self):
        @self.env.with_transaction()
        def try_upgrade(db=None):
            try:
                self.upgrade_environment(db)
            except:
                pass # Already upgraded
    
    def environment_needs_upgrade(self, db):
        cursor = db.cursor()
        try:
            cursor.execute('select count(*) from project_feedback')
            cursor.fetchone()
            return False
        except:
            return True
    
    def upgrade_environment(self, db):
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

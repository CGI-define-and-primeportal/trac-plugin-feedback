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
from trac.config import ListOption
from trac.core import implements
from trac.web.api import IRequestHandler, ITemplateStreamFilter
from trac.env import IEnvironmentSetupParticipant

'''
Created on 14 Sep 2010

@author: enmarkp
'''

class Feedback(Component):
    realms = ListOption('feedback', 'realms', '*',
                        doc="Show feedback option in these realms")
    implements(ITemplateStreamFilter, IRequestHandler, 
               IEnvironmentSetupParticipant)
    
    _schema = [Table('project_feedback')[
                   Column('author'),
                   Column('feedback'),
                   Column('path'),
                   Column('created', type='int64'),
                   Column('modified', type='int64')]]

    # ITemplateStreamFilter
    
    def filter_stream(self, req, method, filename, stream, data):
        return stream
    
    # IRequestHandler
    
    def match_request(self, req):
        return req.path_info == '/feedback'
    
    def process_request(self, req):
        if req.method == 'POST':
            # store feedback
            pass
        else:
            # list user's feedback
            pass
        return 'feedback.html', {}, 'text/html'

    # IEnvironmentSetupParticipant
    
    def environment_created(self):
        @self.env.with_transaction()
        def try_upgrade(db=None):
            self.upgrade_environment(db)
    
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
                

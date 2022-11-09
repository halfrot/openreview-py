from .. import openreview
from openreview.api import Group
from openreview import tools

import os
import json
from tqdm import tqdm

class GroupBuilder(object):

    def __init__(self, venue):
        self.venue = venue
        self.client = venue.client
        self.client_v1 = openreview.Client(baseurl=openreview.tools.get_base_urls(self.client)[0], token=self.client.token)
        self.venue_id = venue.id

    def update_web_field(self, group_id, web):
        return self.post_group(openreview.api.Group(
            id = group_id,
            web = web
        ))


    def post_group(self, group):
        self.client.post_group_edit(
            invitation = self.venue.get_meta_invitation_id() if group.id.startswith(self.venue_id) else 'openreview.net/-/Edit',
            readers = [self.venue_id],
            writers = [self.venue_id],
            signatures = ['~Super_User1' if group.id == self.venue_id else self.venue_id],
            group = group
        )
        return self.client.get_group(group.id)        

    def build_groups(self, venue_id):
        path_components = venue_id.split('/')
        paths = ['/'.join(path_components[0:index+1]) for index, path in enumerate(path_components)]
        groups = []

        for p in paths:
            group = tools.get_group(self.client, id = p)
            if group is None:
                self.client.post_group_edit(
                    invitation = self.venue.get_meta_invitation_id() if venue_id == p else 'openreview.net/-/Edit',
                    readers = ['everyone'],
                    writers = ['~Super_User1'],
                    signatures = ['~Super_User1'],
                    group = Group(
                        id = p,
                        readers = ['everyone'],
                        nonreaders = [],
                        writers = [p],
                        signatories = [p],
                        signatures = ['~Super_User1'],
                        members = [],
                        details = { 'writable': True }
                    )
                )
                group = self.client.get_group(p)
            groups.append(group)

        return groups

    def set_landing_page(self, group, parentGroup):
        # sets webfield to show links to child groups

        children_groups = self.client_v1.get_groups(regex = group.id + '/[^/]+/?$')

        links = []
        for children in children_groups:
            if not group.web or (group.web and children.id not in group.web):
                links.append({ 'url': '/group?id=' + children.id, 'name': children.id})

        if not group.web:
            # create new webfield using template
            header = {
                'title': group.id,
                'description': ''
            }

            with open(os.path.join(os.path.dirname(__file__), 'webfield/landingWebfield.js')) as f:
                content = f.read()
                content = content.replace("var GROUP_ID = '';", "var GROUP_ID = '" + group.id + "';")
                if parentGroup:
                    content = content.replace("var PARENT_GROUP_ID = '';", "var PARENT_GROUP_ID = '" + parentGroup.id + "';")
                content = content.replace("var HEADER = {};", "var HEADER = " + json.dumps(header) + ";")
                content = content.replace("var VENUE_LINKS = [];", "var VENUE_LINKS = " + json.dumps(links) + ";")
                return self.update_web_field(group.id, content)

        elif links:
            # parse existing webfield and add new links
            # get links array without square brackets
            link_str = json.dumps(links)
            link_str = link_str[1:-1]
            start_pos = group.web.find('VENUE_LINKS = [') + len('VENUE_LINKS = [')
            return self.update_web_field(group.id, group.web[:start_pos] +link_str + ','+ group.web[start_pos:])

    
    def get_reviewer_identity_readers(self, number):
        return openreview.stages.IdentityReaders.get_readers(self.venue, number, self.venue.reviewer_identity_readers)

    def get_action_editor_identity_readers(self, number):
        return openreview.stages.IdentityReaders.get_readers(self.venue, number, self.venue.action_editor_identity_readers)

    def get_senior_action_editor_identity_readers(self, number):
        return openreview.stages.IdentityReaders.get_readers(self.venue, number, self.venue.senior_action_editor_identity_readers)

    def get_reviewer_paper_group_readers(self, number):
        readers=[self.venue.id]
        if self.venue.use_senior_action_editors:
            readers.append(self.venue.get_senior_action_editors_id(number))
        if self.venue.use_action_editors:
            readers.append(self.venue.get_action_editors_id(number))
        readers.append(self.venue.get_reviewers_id(number))
        return readers

    def get_reviewer_paper_group_writers(self, number):
        readers=[self.venue.id]
        if self.venue.use_senior_action_editors:
            readers.append(self.venue.get_senior_action_editors_id(number))
        if self.venue.use_action_editors:
            readers.append(self.venue.get_action_editors_id(number))
        return readers


    def get_action_editor_paper_group_readers(self, number):
        readers=[self.venue.id, self.venue.get_editors_in_chief_id()]
        if self.venue.use_senior_action_editors:
            readers.append(self.venue.get_senior_action_editors_id(number))
        readers.append(self.venue.get_action_editors_id(number))
        if openreview.stages.IdentityReaders.REVIEWERS_ASSIGNED in self.venue.action_editor_identity_readers:
            readers.append(self.venue.get_reviewers_id(number))
        return readers

    def create_venue_group(self):

        venue_id = self.venue_id

        groups = self.build_groups(venue_id)
        for i, g in enumerate(groups[:-1]):
            self.set_landing_page(g, groups[i-1] if i > 0 else None)

        venue_group = openreview.api.Group(id = venue_id,
            readers = ['everyone'],
            writers = [venue_id],
            signatures = ['~Super_User1'],
            signatories = [venue_id],
            members = [],
            host = venue_id
        )

        with open(os.path.join(os.path.dirname(__file__), 'webfield/homepageWebfield.js')) as f:
            content = f.read()
            venue_group.web = content
            self.post_group(venue_group)

        self.client_v1.add_members_to_group('venues', venue_id)
        root_id = groups[0].id
        if root_id == root_id.lower():
            root_id = groups[1].id        
        self.client_v1.add_members_to_group('host', root_id)

        content = {
            'submission_id': { 'value': self.venue.get_submission_id() },
            'submission_name': { 'value': self.venue.submission_stage.name },
            'submission_venue_id': { 'value': self.venue.get_submission_venue_id() },
            'withdrawn_venue_id': { 'value': self.venue.get_withdrawn_submission_venue_id() },
            'desk_rejected_venue_id': { 'value': self.venue.get_desk_rejected_submission_venue_id() },
            'public_submissions': { 'value': 'Yes' if self.venue.submission_stage.public else 'No' },
            'public_withdrawn_submissions': { 'value': 'Yes' if self.venue.submission_stage.withdrawn_submission_public else 'No'},
            'public_desk_rejected_submissions': { 'value': 'Yes' if self.venue.submission_stage.desk_rejected_submission_public else 'No' },
            'title': { 'value': self.venue.name if self.venue.name else '' },
            'subtitle': { 'value': self.venue.short_name if self.venue.short_name else '' },
            'website': { 'value': self.venue.website if self.venue.website else '' },
            'contact': { 'value': self.venue.contact if self.venue.contact else '' },
            'editors_in_chief_id': { 'value': self.venue.get_editors_in_chief() },
            'reviewers_id': { 'value': self.venue.get_reviewers_id() },
            'reviewers_custom_max_papers_id': { 'value': self.venue.get_custom_max_papers_id(self.venue.get_reviewers_id()) },
            'reviewers_affinity_score_id': { 'value': self.venue.get_affinity_score_id(self.venue.get_reviewers_id()) },
            'reviewers_conflict_id': { 'value': self.venue.get_conflict_score_id(self.venue.get_reviewers_id()) },
            'reviewers_recruitment_id': { 'value': self.venue.get_recruitment_id(self.venue.get_reviewers_id()) },
            'authors_id': { 'value': self.venue.get_authors_id() },
        }

        if self.venue.use_action_editors:
            content['action_editors_id'] = { 'value': self.venue.get_action_editors_id() }

        if self.venue.use_senior_action_editors:
            content['senior_action_editors_id'] = { 'value': self.venue.get_senior_action_editors_id() }

        if self.venue.bid_stages:
            content['bid_name'] = { 'value': self.venue.bid_stages[0].name }

        if self.venue.review_stage:
            content['review_name'] = { 'value': self.venue.review_stage.name }
            content['review_rating'] = { 'value': self.venue.review_stage.rating_field_name }
            content['review_confidence'] = { 'value': self.venue.review_stage.confidence_field_name }

        if self.venue.meta_review_stage:
            content['meta_review_name'] = { 'value': self.venue.meta_review_stage.name }

        if self.venue.decision_stage:
            content['decision_name'] = { 'value': self.venue.decision_stage.name }

        if self.venue.request_form_id:
            content['request_form_id'] = { 'value': self.venue.request_form_id }

        self.client.post_group_edit(
            invitation = self.venue.get_meta_invitation_id(),
            readers = [self.venue.venue_id],
            writers = [self.venue.venue_id],
            signatures = [self.venue.venue_id],
            group = openreview.api.Group(
                id = self.venue_id,
                content = content
            )
        )        
       
    def create_editors_in_chief_group(self, editor_in_chief_ids=[]):

        venue_id = self.venue_id

        eic_group_id = self.venue.get_editors_in_chief_id()
        eic_group = openreview.tools.get_group(self.client, eic_group_id)
        if not eic_group:
            eic_group=Group(id=eic_group_id,
                            readers=['everyone'],
                            writers=[venue_id, eic_group_id],
                            signatures=[venue_id],
                            signatories=[eic_group_id, venue_id],
                            members=editor_in_chief_ids
                            )
            with open(os.path.join(os.path.dirname(__file__), 'webfield/editorsInChiefWebfield.js')) as f:
                content = f.read()
                eic_group.web = content
                self.post_group(eic_group)

            ## Add pcs to have all the permissions
            self.client.add_members_to_group(venue_id, eic_group_id)        
    
    def create_authors_group(self):

        venue_id = self.venue_id
        ## authors group
        authors_id = self.venue.get_authors_id()
        authors_group = openreview.tools.get_group(self.client, authors_id)
        if not authors_group:
            authors_group = Group(id=authors_id,
                            readers=[venue_id, authors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[])

            with open(os.path.join(os.path.dirname(__file__), 'webfield/authorsWebfield.js')) as f:
                content = f.read()
                authors_group.web = content
                self.post_group(authors_group)

        authors_accepted_id = self.venue.get_authors_accepted_id()
        authors_accepted_group = openreview.tools.get_group(self.client, authors_accepted_id)
        if not authors_accepted_group:
            authors_accepted_group = self.post_group(Group(id=authors_accepted_id,
                            readers=[venue_id, authors_accepted_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]))        
    
    def create_reviewers_group(self):

        venue_id = self.venue.id
        reviewers_id = self.venue.get_reviewers_id()
        action_editors_id = self.venue.get_action_editors_id()
        senior_action_editors_id = self.venue.get_senior_action_editors_id()
        reviewer_group = openreview.tools.get_group(self.client, reviewers_id)
        if not reviewer_group:
            reviewer_group = Group(id=reviewers_id,
                            readers=[venue_id, senior_action_editors_id, action_editors_id, reviewers_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/reviewersWebfield.js')) as f:
                content = f.read()
                reviewer_group.web = content
                self.post_group(reviewer_group)

    def create_action_edtiors_group(self):

        venue_id = self.venue.id
        action_editors_id = self.venue.get_action_editors_id()
        senior_action_editors_id = self.venue.get_senior_action_editors_id()
        area_chairs_group = openreview.tools.get_group(self.client, action_editors_id)
        if not area_chairs_group:
            area_chairs_group = Group(id=action_editors_id,
                            readers=[venue_id, senior_action_editors_id, action_editors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/actioneditorsWebfield.js')) as f:
                content = f.read()
                area_chairs_group.web = content
                self.post_group(area_chairs_group) 

    def create_senior_action_editors_group(self):

        venue_id = self.venue.id
        senior_action_editors_id = self.venue.get_senior_action_editors_id()
        senior_action_editors_group = openreview.tools.get_group(self.client, senior_action_editors_id)
        if not senior_action_editors_group:
            senior_action_editors_group = Group(id=senior_action_editors_id,
                            readers=[venue_id, senior_action_editors_id],
                            writers=[venue_id],
                            signatures=[venue_id],
                            signatories=[venue_id],
                            members=[]
                        )

            with open(os.path.join(os.path.dirname(__file__), 'webfield/actioneditorsWebfield.js')) as f:
                content = f.read()
                senior_action_editors_group.web = content
                self.post_group(senior_action_editors_group)

    def create_paper_committee_groups(self, submissions, overwrite=False):

        group_by_id = { g.id: g for g in self.client.get_all_groups(prefix=f'{self.venue.id}/{self.venue.submission_stage.name}.*') }

        def create_paper_commmitee_group(note):
            # Reviewers Paper group
            reviewers_id=self.venue.get_reviewers_id(number=note.number)
            group = group_by_id.get(reviewers_id)
            if not group or overwrite:
                self.post_group(openreview.api.Group(id=reviewers_id,
                    readers=self.get_reviewer_paper_group_readers(note.number),
                    nonreaders=[self.venue.get_authors_id(note.number)],
                    deanonymizers=self.get_reviewer_identity_readers(note.number),
                    writers=self.get_reviewer_paper_group_writers(note.number),
                    signatures=[self.venue.id],
                    signatories=[self.venue.id],
                    anonids=True,
                    members=group.members if group else []
                ))

            # Reviewers Submitted Paper group
            reviewers_submitted_id = self.venue.get_reviewers_id(number=note.number) + '/Submitted'
            group = group_by_id.get(reviewers_submitted_id)
            if not group or overwrite:
                readers=[self.venue.id]
                if self.venue.use_senior_action_editors:
                    readers.append(self.venue.get_senior_action_editors_id(note.number))
                if self.venue.use_action_editors:
                    readers.append(self.venue.get_action_editors_id(note.number))
                readers.append(reviewers_submitted_id)
                self.post_group(openreview.api.Group(id=reviewers_submitted_id,
                    readers=readers,
                    writers=[self.venue.id],
                    signatures=[self.venue.id],
                    signatories=[self.venue.id],
                    members=group.members if group else []
                ))

            # Area Chairs Paper group
            if self.venue.use_action_editors:
                action_editors_id=self.venue.get_action_editors_id(number=note.number)
                group = group_by_id.get(action_editors_id)
                if not group or overwrite:
                    self.post_group(openreview.api.Group(id=action_editors_id,
                        readers=self.get_area_chair_paper_group_readers(note.number),
                        nonreaders=[self.venue.get_authors_id(note.number)],
                        deanonymizers=self.get_area_chair_identity_readers(note.number),
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        signatories=[self.venue.id],
                        anonids=True,
                        members=group.members if group else []
                    ))

            # Senior Area Chairs Paper group
            if self.venue.use_senior_action_editors:
                senior_action_editors_id=self.venue.get_senior_action_editors_id(number=note.number)
                group = group_by_id.get(senior_action_editors_id)
                if not group or overwrite:
                    self.post_group(openreview.api.Group(id=senior_action_editors_id,
                        readers=self.get_senior_area_chair_identity_readers(note.number),
                        nonreaders=[self.venue.get_authors_id(note.number)],
                        writers=[self.venue.id],
                        signatures=[self.venue.id],
                        signatories=[self.venue.id, senior_action_editors_id],
                        members=group.members if group else []
                    ))

        openreview.tools.concurrent_requests(create_paper_commmitee_group, submissions, desc='create_paper_committee_groups')

    def create_recruitment_committee_groups(self, committee_name):

        venue_id = self.venue.venue_id

        eic_group_id = self.venue.get_editors_in_chief()
        committee_id = self.venue.get_committee_id(committee_name)
        committee_invited_id = self.venue.get_committee_id_invited(committee_name)
        committee_declined_id = self.venue.get_committee_id_declined(committee_name)

        committee_group = tools.get_group(self.client, committee_id)
        if not committee_group:
            committee_group=self.post_group(Group(id=committee_id,
                            readers=[venue_id, committee_id],
                            writers=[venue_id, eic_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_id],
                            members=[]
                            ))

        committee_declined_group = tools.get_group(self.client, committee_declined_id)
        if not committee_declined_group:
            committee_declined_group=self.post_group(Group(id=committee_declined_id,
                            readers=[venue_id, committee_declined_id],
                            writers=[venue_id, eic_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_declined_id],
                            members=[]
                            ))

        committee_invited_group = tools.get_group(self.client, committee_invited_id)
        if not committee_invited_group:
            committee_invited_group=self.post_group(Group(id=committee_invited_id,
                            readers=[venue_id, committee_invited_id],
                            writers=[venue_id, eic_group_id],
                            signatures=[venue_id],
                            signatories=[venue_id, committee_invited_id],
                            members=[]
                            ))

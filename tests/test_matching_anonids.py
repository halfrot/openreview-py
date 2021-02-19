from __future__ import absolute_import, division, print_function, unicode_literals
import openreview
import pytest
import requests
import datetime
import time
import os
import re
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import NoSuchElementException


class TestMatchingWithAnonIds():

    @pytest.fixture(scope="class")
    def pc_client(self):
        return openreview.Client(username='pc1@uai.com', password='1234')

    @pytest.fixture(scope="class")
    def conference(self, client, helpers):
        pc_client = helpers.create_user('pc1@uai.com', 'TestPC', 'UAI')
        builder = openreview.conference.ConferenceBuilder(client)
        builder.set_conference_id('auai.org/UAI/2021/Conference')
        builder.set_conference_name('Conference on Uncertainty in Artificial Intelligence')
        builder.set_conference_short_name('UAI 2021')
        builder.set_homepage_header({
        'title': 'UAI 2021',
        'subtitle': 'Conference on Uncertainty in Artificial Intelligence',
        'deadline': 'Abstract Submission Deadline: 11:59 pm Samoa Standard Time, March 4, 2021, Full Submission Deadline: 11:59 pm Samoa Standard Time, March 8, 2021',
        'date': 'July 22 - July 25, 2021',
        'website': 'http://auai.org/uai2021/',
        'location': 'Tel Aviv, Israel',
        'instructions': '''<p><strong>Important Information about Anonymity:</strong><br>
            When you post a submission to UAI 2021, please provide the real names and email addresses of authors in the submission form below (but NOT in the manuscript).
            The <em>original</em> record of your submission will be private, and will contain your real name(s).
            The PDF in your submission should not contain the names of the authors. </p>
            <p><strong>Conflict of Interest:</strong><br>
            Please make sure that your current and previous affiliations listed on your OpenReview <a href=\"/profile\">profile page</a> is up-to-date to avoid conflict of interest.</p>
            <p><strong>Questions or Concerns:</strong><br> Please contact the UAI 2021 Program chairs at <a href=\"mailto:uai2021chairs@gmail.com\">uai2021chairs@gmail.com</a>.
            <br>Please contact the OpenReview support team at <a href=\"mailto:info@openreview.net\">info@openreview.net</a> with any OpenReview related questions or concerns.
            </p>'''
        })
        print ('Homepage header set')
        builder.set_conference_program_chairs_ids(['pc1@uai.com', 'pc4@mail.com'])
        builder.set_conference_area_chairs_name('Senior_Program_Committee')
        builder.set_conference_reviewers_name('Program_Committee')
        now = datetime.datetime.utcnow()
        builder.set_submission_stage(due_date = now + datetime.timedelta(minutes = 40), double_blind= True, subject_areas=[
            "Algorithms: Approximate Inference",
            "Algorithms: Belief Propagation",
            "Algorithms: Distributed and Parallel",
            "Algorithms: Exact Inference",
        ])
        additional_registration_content = {
            'reviewing_experience': {
                'description': 'How many times have you been a reviewer for any conference or journal?',
                'value-radio': [
                    'Never - this is my first time',
                    '1 time - building my reviewer skills',
                    '2-4 times  - comfortable with the reviewing process',
                    '5-10 times  - active community citizen',
                    '10+ times  - seasoned reviewer'
                ],
                'order': 5,
                'required': False
            }
        }
        builder.set_registration_stage(due_date = now + datetime.timedelta(minutes = 40), ac_additional_fields = additional_registration_content)

        builder.set_bid_stage('auai.org/UAI/2021/Conference/Program_Committee', due_date = now + datetime.timedelta(minutes = 40), request_count = 50)
        builder.set_bid_stage('auai.org/UAI/2021/Conference/Senior_Program_Committee', due_date = now + datetime.timedelta(minutes = 40), request_count = 50)
        conference = builder.get_result()
        return conference

    def test_setup_matching(self, conference, pc_client, test_client, helpers):

        ## Set committee
        conference.set_area_chairs(['ac2@cmu.edu', 'ac2@umass.edu'])
        conference.set_reviewers(['r3@mit.edu', 'r3@google.com', 'r3@fb.com'])

        ## Paper 1
        note_1 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'test@mail.com', 'a1@cmu.edu'],
            writers = [conference.id, '~Test_User1', 'test@mail.com', 'a1@cmu.edu'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 1',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a1@cmu.edu'],
                'authors': ['Test User', 'Author 1'],
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Belief Propagation'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_1.content['pdf'] = url
        note_1 = test_client.post_note(note_1)

        ## Paper 2
        note_2 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'test@mail.com', 'a2@mit.edu'],
            writers = [conference.id, '~Test_User1', 'test@mail.com', 'a2@mit.edu'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 2',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a2@mit.edu'],
                'authors': ['Test User', 'Author 2'],
                'subject_areas': [
                    'Algorithms: Approximate Inference',
                    'Algorithms: Exact Inference'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_2.content['pdf'] = url
        note_2 = test_client.post_note(note_2)

        ## Paper 3
        note_3 = openreview.Note(invitation = conference.get_submission_id(),
            readers = ['~Test_User1', 'test@mail.com', 'a3@umass.edu'],
            writers = [conference.id, '~Test_User1', 'test@mail.com', 'a3@umass.edu', 'pc3@mail.com'],
            signatures = ['~Test_User1'],
            content = {
                'title': 'Paper title 3',
                'abstract': 'This is an abstract',
                'authorids': ['test@mail.com', 'a3@umass.edu', 'pc3@mail.com'],
                'authors': ['Test User', 'Author 3', 'PC author'],
                'subject_areas': [
                    'Algorithms: Distributed and Parallel',
                    'Algorithms: Exact Inference'
                ]
            }
        )
        url = test_client.put_attachment(os.path.join(os.path.dirname(__file__), 'data/paper.pdf'), conference.get_submission_id(), 'pdf')
        note_3.content['pdf'] = url
        note_3 = test_client.post_note(note_3)

        ## Create blind submissions
        conference.setup_post_submission_stage(force=True)
        blinded_notes = conference.get_submissions()

        ac1_client = helpers.create_user('ac2@cmu.edu', 'AreaChair', 'CMUOne')
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_area_chairs_id()),
            readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            writers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            signatures = ['~AreaChair_CMUOne1'],
            head = blinded_notes[0].id,
            tail = '~AreaChair_CMUOne1',
            label = 'High'
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_area_chairs_id()),
            readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            writers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            signatures = ['~AreaChair_CMUOne1'],
            head = blinded_notes[1].id,
            tail = '~AreaChair_CMUOne1',
            label = 'Low'
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_area_chairs_id()),
            readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            writers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            signatures = ['~AreaChair_CMUOne1'],
            head = blinded_notes[2].id,
            tail = '~AreaChair_CMUOne1',
            label = 'Very Low'
        ))

        r1_client = helpers.create_user('r3@mit.edu', 'Reviewer', 'MITOne')
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = ['auai.org/UAI/2021/Conference', '~Reviewer_MITOne1'],
            writers = ['auai.org/UAI/2021/Conference', '~Reviewer_MITOne1'],
            signatures = ['~Reviewer_MITOne1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_MITOne1',
            label = 'Neutral'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = ['auai.org/UAI/2021/Conference', '~Reviewer_MITOne1'],
            writers = ['auai.org/UAI/2021/Conference', '~Reviewer_MITOne1'],
            signatures = ['~Reviewer_MITOne1'],
            head = blinded_notes[1].id,
            tail = '~Reviewer_MITOne1',
            label = 'Very High'
        ))
        r1_client.post_edge(openreview.Edge(invitation = conference.get_bid_id(conference.get_reviewers_id()),
            readers = ['auai.org/UAI/2021/Conference', '~Reviewer_MITOne1'],
            writers = ['auai.org/UAI/2021/Conference', '~Reviewer_MITOne1'],
            signatures = ['~Reviewer_MITOne1'],
            head = blinded_notes[2].id,
            tail = '~Reviewer_MITOne1',
            label = 'Low'
        ))

        # Set up reviewer matching
        conference.setup_matching(build_conflicts=True)


        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Paper_Assignment')

        # Set up AC matching
        conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts=True)

        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_CMUOne1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict',
            tail='~Reviewer_MITOne1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict',
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'


    def test_setup_matching_with_tpms(self, conference, pc_client, helpers):

        # Set up reviewer matching
        conference.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'), build_conflicts=True)

        print(conference.get_reviewers_id())

        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/-/Recommendation' not in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Paper_Assignment')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score')

        # Set up ac matching
        conference.setup_matching(
            committee_id=conference.get_area_chairs_id(),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'),
            build_conflicts=True)

        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Aggregate_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/TPMS_Score')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict', tail='~AreaChair_CMUOne1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict', tail='~Reviewer_MITOne1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict', tail = 'ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51


    def test_setup_matching_with_recommendations(self, conference, pc_client, test_client, helpers):

        blinded_notes = list(conference.get_submissions())

        ## Open reviewer recommendations
        now = datetime.datetime.utcnow()
        conference.open_recommendations(assignment_title='', due_date = now + datetime.timedelta(minutes = 40))

        ## Recommend reviewers
        ac1_client = helpers.get_user('ac2@cmu.edu')
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            signatures = ['~AreaChair_CMUOne1'],
            writers = ['~AreaChair_CMUOne1'],
            head = blinded_notes[0].id,
            tail = '~Reviewer_MITOne1',
            weight = 1
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            signatures = ['~AreaChair_CMUOne1'],
            writers = ['~AreaChair_CMUOne1'],
            head = blinded_notes[1].id,
            tail = 'r3@google.com',
            weight = 2
        ))
        ac1_client.post_edge(openreview.Edge(invitation = conference.get_recommendation_id(),
            readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
            signatures = ['~AreaChair_CMUOne1'],
            writers = ['~AreaChair_CMUOne1'],
            head = blinded_notes[1].id,
            tail = 'r3@fb.com',
            weight = 3
        ))

       # Set up reviewer matching
        conference.setup_matching(tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/reviewer_tpms_scores.csv'), build_conflicts=True)

        print(conference.get_reviewers_id())

        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')

        # Set up ac matching
        conference.setup_matching(
            committee_id=conference.get_area_chairs_id(),
            tpms_score_file=os.path.join(os.path.dirname(__file__), 'data/ac_tpms_scores.csv'),
            build_conflicts=True)

        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Assignment_Configuration')
        assert invitation
        assert 'scores_specification' in invitation.reply['content']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Bid' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/TPMS_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score' in invitation.reply['content']['scores_specification']['default']
        assert 'auai.org/UAI/2021/Conference/Program_Committee/-/Recommendation' in invitation.reply['content']['scores_specification']['default']

        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        recommendations = pc_client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict', tail='~AreaChair_CMUOne1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict', tail='~Reviewer_MITOne1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict', tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51


    def test_setup_matching_with_subject_areas(self, conference, pc_client, test_client, helpers):

        blinded_notes = list(conference.get_submissions())

        registration_notes = pc_client.get_notes(invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Form')
        assert registration_notes
        assert len(registration_notes) == 1

        registration_forum = registration_notes[0].forum

        ## Recommend reviewers
        ac1_client = helpers.get_user('ac2@cmu.edu')
        ac1_client.post_note(
            openreview.Note(
                invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Registration',
                readers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
                writers = ['auai.org/UAI/2021/Conference', '~AreaChair_CMUOne1'],
                signatures = ['~AreaChair_CMUOne1'],
                forum = registration_forum,
                replyto = registration_forum,
                content = {
                    'subject_areas': [
                        'Algorithms: Approximate Inference',
                        'Algorithms: Belief Propagation'
                    ],
                    'profile_confirmed': 'Yes',
                    'expertise_confirmed': 'Yes',
                    'reviewing_experience': '2-4 times  - comfortable with the reviewing process'
                }))

        # Set up reviewer matching
        conference.setup_matching(build_conflicts=True)

        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Subject_Areas_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')

        # Set up AC matching
        conference.setup_matching(committee_id=conference.get_area_chairs_id(), build_conflicts=True)

        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert pc_client.get_invitation(id='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_area_chairs_id()))
        assert bids
        assert 3 == len(bids)

        bids = pc_client.get_edges(invitation = conference.get_bid_id(conference.get_reviewers_id()))
        assert bids
        assert 3 == len(bids)

        recommendations = pc_client.get_edges(invitation = conference.get_recommendation_id())
        assert recommendations
        assert 3 == len(recommendations)

        reviewer_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Custom_Max_Papers')
        assert not reviewer_custom_loads

        ac_custom_loads = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Custom_Max_Papers')
        assert not ac_custom_loads

        reviewer_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict')
        assert 1 == len(reviewer_conflicts)

        ac_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict')
        assert 2 == len(ac_conflicts)

        ac1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict',
            tail='~AreaChair_CMUOne1')
        assert ac1_conflicts
        assert len(ac1_conflicts)
        assert ac1_conflicts[0].label == 'Conflict'

        r1_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Conflict',
            tail='~Reviewer_MITOne1')
        assert r1_conflicts
        assert len(r1_conflicts)
        assert r1_conflicts[0].label == 'Conflict'

        ac2_conflicts = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Conflict',
            tail='ac2@umass.edu')
        assert ac2_conflicts
        assert len(ac2_conflicts)
        assert ac2_conflicts[0].label == 'Conflict'

        submissions = conference.get_submissions()
        assert submissions
        assert 3 == len(submissions)

        reviewer_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score')
        assert 9 == len(reviewer_tpms_scores)

        ac_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/TPMS_Score')
        assert 6 == len(ac_tpms_scores)

        r3_s0_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[0].id)
        assert r3_s0_tpms_scores
        assert 1 == len(r3_s0_tpms_scores)
        assert r3_s0_tpms_scores[0].weight == 0.21

        r3_s1_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[1].id)
        assert r3_s1_tpms_scores
        assert 1 == len(r3_s1_tpms_scores)
        assert r3_s1_tpms_scores[0].weight == 0.31

        r3_s2_tpms_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/TPMS_Score',
            tail='r3@fb.com',
            head=submissions[2].id)
        assert r3_s2_tpms_scores
        assert 1 == len(r3_s2_tpms_scores)
        assert r3_s2_tpms_scores[0].weight == 0.51

        reviewer_subject_area_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Subject_Areas_Score')
        assert not reviewer_subject_area_scores

        ac_subject_areas_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score')
        assert 3 == len(ac_subject_areas_scores)

        ac1_s0_subject_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_CMUOne1',
            head=submissions[0].id)
        assert ac1_s0_subject_scores
        assert 1 == len(ac1_s0_subject_scores)
        assert ac1_s0_subject_scores[0].weight ==  0

        ac1_s1_subject_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_CMUOne1',
            head=submissions[1].id)
        assert ac1_s1_subject_scores
        assert 1 == len(ac1_s1_subject_scores)
        assert ac1_s1_subject_scores[0].weight ==  0.3333333333333333

        ac1_s2_subject_scores = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Subject_Areas_Score',
            tail='~AreaChair_CMUOne1',
            head=submissions[2].id)
        assert ac1_s2_subject_scores
        assert 1 == len(ac1_s2_subject_scores)
        assert ac1_s2_subject_scores[0].weight ==  1

    def test_set_assigments(self, conference, pc_client, test_client, helpers):

        conference.client = pc_client

        blinded_notes = list(conference.get_submissions())

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Paper_Assignment',
            label='rev-matching'
        )
        assert 0 == len(edges)

        #Reviewer assignments
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@mit.edu',
            label = 'rev-matching',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@google.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@google.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r3@google.com',
            label = 'rev-matching',
            weight = 0.87
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r3@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r3@fb.com',
            label = 'rev-matching',
            weight = 0.94
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r3@mit.edu',
            label = 'rev-matching',
            weight = 0.98
        ))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Paper_Assignment',
            label='rev-matching'
        )
        assert 6 == len(edges)

        conference.set_assignments(assignment_title='rev-matching')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert 2 == len(revs_paper0.members)
        assert 'r3@mit.edu' in revs_paper0.members
        assert 'r3@google.com' in revs_paper0.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[0].number))
        assert len(anon_groups) == 2
        anon_members = [ a.members[0] for a in anon_groups]
        assert 'r3@mit.edu' in anon_members
        assert 'r3@google.com' in anon_members

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert 2 == len(revs_paper1.members)
        assert 'r3@fb.com' in revs_paper1.members
        assert 'r3@google.com' in revs_paper1.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[1].number))
        assert len(anon_groups) == 2
        anon_members = [ a.members[0] for a in anon_groups]
        assert 'r3@fb.com' in anon_members
        assert 'r3@google.com' in anon_members

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert 2 == len(revs_paper2.members)
        assert 'r3@fb.com' in revs_paper2.members
        assert 'r3@mit.edu' in revs_paper2.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[2].number))
        assert len(anon_groups) == 2
        anon_members = [ a.members[0] for a in anon_groups]
        assert 'r3@fb.com' in anon_members
        assert 'r3@mit.edu' in anon_members

    def test_redeploy_assigments(self, conference, client, pc_client, test_client, helpers):

        blinded_notes = list(conference.get_submissions())

        #Reviewer assignments
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@fb.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r3@mit.edu',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@google.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r3@google.com',
            label = 'rev-matching-new',
            weight = 0.98
        ))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Program_Committee/-/Paper_Assignment',
            label='rev-matching-new'
        )
        assert 3 == len(edges)

        conference.set_assignments(assignment_title='rev-matching-new', overwrite=True)

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com'] == revs_paper0.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[0].number))
        assert len(anon_groups) == 3
        anon_members = [ a.members[0] for a in anon_groups]
        assert 'r3@fb.com' in anon_members
        assert 'r3@mit.edu' in anon_members
        assert 'r3@google.com' in anon_members

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['r3@mit.edu'] == revs_paper1.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[1].number))
        assert len(anon_groups) == 3
        assert 'r3@fb.com' in anon_members
        assert 'r3@google.com' in anon_members
        assert 'r3@mit.edu' in anon_members

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r3@google.com'] == revs_paper2.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[2].number))
        assert len(anon_groups) == 3
        anon_members = [ a.members[0] for a in anon_groups]
        assert 'r3@fb.com' in anon_members
        assert 'r3@mit.edu' in anon_members
        assert 'r3@google.com' in anon_members

        ## Emergency reviewers, append reviewers
        conference.set_reviewers(['r3@mit.edu', 'r3@google.com', 'r3@fb.com', 'r2@mit.edu'])
        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@mit.edu',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r2@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r2@mit.edu',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@google.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r3@google.com',
            label = 'rev-matching-emergency',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com', 'r3@mit.edu', 'r2@mit.edu'] == revs_paper0.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[0].number))
        assert len(anon_groups) == 4

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['r3@mit.edu', 'r3@google.com'] == revs_paper1.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[1].number))
        assert len(anon_groups) == 3

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r3@google.com'] == revs_paper2.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[2].number))
        assert len(anon_groups) == 3

        pc_client.remove_members_from_group('auai.org/UAI/2021/Conference/Paper3/Program_Committee', ['r3@mit.edu'])

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@google.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@google.com',
            label = 'rev-matching-emergency-2',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency-2')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com', 'r2@mit.edu', 'r3@google.com'] == revs_paper0.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[0].number))
        assert len(anon_groups) == 4

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['r3@mit.edu', 'r3@google.com'] == revs_paper1.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[1].number))
        assert len(anon_groups) == 3

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r3@google.com'] == revs_paper2.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[2].number))
        assert len(anon_groups) == 3

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@google.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r3@google.com',
            label = 'rev-matching-emergency-3',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True)

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert [] == revs_paper0.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[0].number))
        assert len(anon_groups) == 4

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert [] == revs_paper1.members

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r3@google.com'] == revs_paper2.members

        now = datetime.datetime.now()
        conference.set_review_stage(openreview.ReviewStage(start_date = now))

        invitation = pc_client.get_invitation(id='auai.org/UAI/2021/Conference/-/Official_Review')
        assert invitation

        conference.set_assignments(assignment_title='rev-matching-emergency-3', overwrite=True)

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert [] == revs_paper0.members

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert [] == revs_paper1.members

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r3@google.com'] == revs_paper2.members
        anon_groups = pc_client.get_groups(regex=conference.get_id()+'/Paper{x}/Program_Committee_'.format(x=blinded_notes[2].number), signatory='r3@google.com')
        assert len(anon_groups) == 1

        reviewer_client = helpers.create_user('r3@google.com', 'Reviewer', 'Two')

        review_note = reviewer_client.post_note(openreview.Note(
            invitation='auai.org/UAI/2021/Conference/Paper1/-/Official_Review',
            forum=blinded_notes[2].id,
            replyto=blinded_notes[2].id,
            content={
                'title': 'review',
                'review': 'this is a good paper',
                'rating': '1: Trivial or wrong',
                'confidence': "1: The reviewer's evaluation is an educated guess"
            },
            readers=[
                "auai.org/UAI/2021/Conference/Program_Chairs",
                "auai.org/UAI/2021/Conference/Paper1/Senior_Program_Committee",
                anon_groups[0].id
            ],
            nonreaders=["auai.org/UAI/2021/Conference/Paper1/Authors"],
            writers=[
                "auai.org/UAI/2021/Conference",
                anon_groups[0].id
            ],
            signatures=[anon_groups[0].id]
        ))

        helpers.await_queue()
        process_logs = client.get_process_logs(id = review_note.id)
        assert len(process_logs) == 1
        assert process_logs[0]['status'] == 'ok'

        pc_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'r3@mit.edu',
            label = 'rev-matching-emergency-4',
            weight = 0.98
        ))

        with pytest.raises(openreview.OpenReviewException, match=r'Can not overwrite assignments when there are reviews posted.'):
            conference.set_assignments(assignment_title='rev-matching-emergency-4', overwrite=True)

    def test_set_reviewers_assignments_as_author(self, conference, pc_client, helpers):

        pc2_client = helpers.create_user('pc4@mail.com', 'PC', 'Four')
        pc2_client.impersonate(conference.id)

        conference.client = pc2_client

        blinded_notes = list(conference.get_submissions())

        pc2_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@mit.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'r3@mit.edu',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        pc2_client.post_edge(openreview.Edge(invitation = conference.get_paper_assignment_id(conference.get_reviewers_id()),
            readers = [conference.id, 'r3@fb.com'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'r3@fb.com',
            label = 'rev-matching-emergency-6',
            weight = 0.98
        ))

        conference.set_assignments(assignment_title='rev-matching-emergency-6')

        revs_paper0 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[0].number))
        assert ['r3@fb.com'] == revs_paper0.members

        revs_paper1 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[1].number))
        assert ['r3@mit.edu'] == revs_paper1.members

        revs_paper2 = pc_client.get_group(conference.get_id()+'/Paper{x}/Program_Committee'.format(x=blinded_notes[2].number))
        assert ['r3@google.com'] == revs_paper2.members


    def test_set_ac_assigments(self, conference, pc_client, test_client, helpers):

        conference.set_area_chairs(['ac2@cmu.edu', 'ac2@umass.edu'])
        blinded_notes = list(conference.get_submissions())

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            label='ac-matching'
        )
        assert 0 == len(edges)

        #AC assignments
        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            readers = [conference.id, 'ac2@cmu.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'ac2@cmu.edu',
            label = 'ac-matching',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            readers = [conference.id, 'ac2@umass.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'ac2@umass.edu',
            label = 'ac-matching',
            weight = 0.87
        ))

        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            readers = [conference.id, 'ac2@umass.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[2].id,
            tail = 'ac2@umass.edu',
            label = 'ac-matching',
            weight = 0.87
        ))

        edges = pc_client.get_edges(
            invitation='auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            label='ac-matching'
        )
        assert 3 == len(edges)

        conference.set_assignments(assignment_title='ac-matching', is_area_chair=True)

        assert pc_client.get_group('auai.org/UAI/2021/Conference/Paper1/Senior_Program_Committee').members == ['ac2@umass.edu']
        assert pc_client.get_groups(regex='auai.org/UAI/2021/Conference/Paper1/Senior_Program_Committee_')

        assert pc_client.get_group('auai.org/UAI/2021/Conference/Paper2/Senior_Program_Committee').members == ['ac2@umass.edu']
        assert pc_client.get_groups(regex='auai.org/UAI/2021/Conference/Paper2/Senior_Program_Committee_')

        assert pc_client.get_group('auai.org/UAI/2021/Conference/Paper3/Senior_Program_Committee').members == ['ac2@cmu.edu']
        assert pc_client.get_groups(regex='auai.org/UAI/2021/Conference/Paper3/Senior_Program_Committee_')


        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            readers = [conference.id, 'ac2@cmu.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[1].id,
            tail = 'ac2@cmu.edu',
            label = 'ac-matching-2',
            weight = 0.98
        ))

        pc_client.post_edge(openreview.Edge(invitation = 'auai.org/UAI/2021/Conference/Senior_Program_Committee/-/Paper_Assignment',
            readers = [conference.id, 'ac2@umass.edu'],
            writers = [conference.id],
            signatures = [conference.id],
            head = blinded_notes[0].id,
            tail = 'ac2@umass.edu',
            label = 'ac-matching-2',
            weight = 0.87
        ))

        conference.set_assignments(assignment_title='ac-matching-2', is_area_chair=True, overwrite=True)

        assert pc_client.get_group('auai.org/UAI/2021/Conference/Paper3/Senior_Program_Committee').members == ['ac2@umass.edu']

        assert pc_client.get_group('auai.org/UAI/2021/Conference/Paper2/Senior_Program_Committee').members == ['ac2@cmu.edu']

        assert pc_client.get_group('auai.org/UAI/2021/Conference/Paper1/Senior_Program_Committee').members == []

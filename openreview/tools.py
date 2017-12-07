#!/usr/bin/python
import openreview

super_user_id = 'OpenReview.net'

def get_profile(client, value):
    profile = None
    try:
        profile = client.get_profile(value)
    except openreview.OpenReviewException as e:
        # throw an error if it is something other than "not found"
        if e[0][0] != 'Profile not found':
            print "OpenReviewException: {0}".format(e)
            return e
    return profile

def create_profile(client, email, first, last, middle = None):

	profile = get_profile(client, email)

	if not profile:
		response = client.get_tildeusername(first, last, middle)
		tilde_id = response['username'].encode('utf-8')

		if tilde_id.endswith(last + '1'):

			tilde_group = openreview.Group(id = tilde_id, signatures = [super_user_id], signatories = [tilde_id], readers = [tilde_id], writers = [super_user_id], members = [email])
			email_group = openreview.Group(id = email, signatures = [super_user_id], signatories = [email], readers = [email], writers = [super_user_id], members = [tilde_id])
			profile_content = {
		        'emails': [email],
		        'preferred_email': email,
		        'names': [
		            {
		                'first': first,
		                'middle': middle,
		                'last': last,
		                'username': tilde_id
		            }
		        ]
		    }
			client.post_group(tilde_group)
			client.post_group(email_group)
			profile = client.post_profile(tilde_id, profile_content)

			return profile

		else:
			raise openreview.OpenReviewException('There is already a profile with this first, middle and last name')
	else:
		raise openreview.OpenReviewException('There is already a profile with this email: ' + email)



from django.test import TestCase
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.core import mail
from rest_framework import status
# Create your tests here.
from ideas_place.models import Idea, Likes

_usermodel = get_user_model()


def get_activation_info(body_string=None):
    try:
        url_start_char_position = body_string.index('http')
    except:
        return None
    parts = body_string[url_start_char_position:].replace('\n', '').split('/')
    uid = parts[-3]
    token = parts[-2]
    return {'uid': uid, 'token': token}


class IdeaModelTestCase(TestCase):
    def setUp(self):
        self.first_user = _usermodel(username="first_user", email="qqq@qqq.com", password='PpPp123456', is_active=True)
        self.first_idea = Idea(i_title='First idea Title', i_text="First idea text")

    def test_model_can_create_user_and_idea(self):
        print('test_model_can_create_user_and_idea -1')
        users_count_before = _usermodel.objects.count()
        self.first_user.save()
        users_count_after = _usermodel.objects.count()
        self.assertNotEqual(users_count_before, users_count_after)

        ideas_count_before = Idea.objects.count()
        self.first_idea.save()
        ideas_count_after = Idea.objects.count()
        self.assertNotEqual(ideas_count_before, ideas_count_after)


class AccountCreationTest(APITestCase):

    def setUp(self) -> None:
        self.test_user = _usermodel.objects.create_user('testuser', 'test@example.com', 'Testpassword123')

        # URL for creating an account.
        self.create_user_url = reverse('rest_api:users-add')
        # URL for activation an account.
        self.activate_user_api_url = reverse('rest_api:user-activate')
        self.get_token_url = reverse('token_obtain_pair')
        self.get_user_1_info = reverse('rest_api:user-detail', kwargs={'pk': 1})
        self.get_user_2_info = reverse('rest_api:user-detail', kwargs={'pk': 2})

        self.get_wrong_user_nfo = reverse('rest_api:user-detail', kwargs={'pk': 200})
        # right user credentials
        self.right_auth_data = {"username": "adminadmin", "password": "PpPp123456"}

    def test_user_signup(self):
        print('test_user_signup-2')
        right_data = {"new_user":
                          {"username": "adminadmin", "email": "ee2020@gmail.com", 'password': 'PpPp123456'}}
        wrong_email_data = {"new_user":
                                {"username": "adminadmin", "email": "ee2010", 'password': 'PpPp123456'}}
        wrong_password_data = {"new_user":
                                   {"username": "adminadmin", "email": "ee2010@gmail.com", 'password': 'Pp'}}

        # ---------- right user signup
        response = self.client.post(self.create_user_url, right_data, format='json')
        self.assertIn('success', response.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ---------- user signup with the same credentials
        response = self.client.post(self.create_user_url, right_data, format='json')
        self.assertNotIn('success', response.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # ---------- We want to make sure we have two users in the database..
        self.assertEqual(_usermodel.objects.count(), 2)

        # ---------- attempt to get token without user activation
        response = self.client.post(self.get_token_url, self.right_auth_data, format='json')
        self.assertContains(response, 'No active account found with the given credentials', status_code=401)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ---------- We want to make sure confirmation message is sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Mail confirmation message')

        # ---------- Attempt to activate account
        # with wrong data
        wrong_data = {'activation': {'uid': "asdsadas", 'token': "khiuehryiewuriuweyriweyriwuyrieuw876"}}
        response = self.client.post(self.activate_user_api_url, wrong_data, format='json')
        self.assertNotContains(response, 'success', status_code=status.HTTP_400_BAD_REQUEST)

        # with right data
        # fetch right activation uid and token from the mail body
        data = {'activation': get_activation_info(mail.outbox[0].body)}
        response = self.client.post(self.activate_user_api_url, data, format='json')
        self.assertContains(response, 'success', status_code=status.HTTP_200_OK)

        # ---------- attempt to get token after user activation
        response = self.client.post(self.get_token_url, self.right_auth_data, format='json')
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        access_token = response.data.get('access')

        # ---------- attempt to get another user's information with auth token
        user_brief_right_data = {'author': {'username': 'testuser', 'ideas': []}}
        # set request's auth header
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(access_token))
        response = self.client.get(self.get_user_1_info, format='json')
        self.assertEqual(user_brief_right_data, response.data)

        # ---------- attempt to get user's himself information with auth token
        user_full_right_data = {'author': {'username': 'adminadmin', 'email': 'ee2020@gmail.com', 'ideas': []}}
        response = self.client.get(self.get_user_2_info, format='json')
        self.assertEqual(user_full_right_data, response.data)

        # ---------- attempt to get information for nonexistent user with auth token
        response = self.client.get(self.get_wrong_user_nfo, format='json')
        self.assertContains(response, 'Not found', status_code=status.HTTP_404_NOT_FOUND)


class IdeaCreatingTest(APITestCase):

    def setUp(self):
        self.test_user1 = _usermodel.objects.create_user(username='testuser',
                                                         email='test@example.com',
                                                         password='Testpassword123',
                                                         is_active=True)
        self.test_user2 = _usermodel.objects.create_user(username='adminadmin',
                                                         email='ee2010@gmail.com',
                                                         password="PpPp123456",
                                                         is_active=True)

        self.token_user1 = self.client.post(reverse('token_obtain_pair'),
                                            {'username': 'testuser', 'password': 'Testpassword123', },
                                            format='json').data['access']

        self.token_user2 = self.client.post(reverse('token_obtain_pair'),
                                            {'username': 'adminadmin', 'password': 'PpPp123456', },
                                            format='json').data['access']

        self.create_user_idea = reverse('rest_api:idea-tool')

        # ---------- user 1 Ideas list
        self.user1_ideas = [{'i_title': 'U1 First title', 'i_text': 'U1 I1 text'},
                            {'i_title': 'U1 Second title', 'i_text': 'U1 I2 text'},
                            {'i_title': 'U1 Third title', 'i_text': 'U1 I3 text'}
                            ]

        # ---------- user 2 Ideas list
        self.user2_ideas = [{'i_title': 'U2 First title', 'i_text': 'U2 I1 text'},
                            {'i_title': 'U2 Second title', 'i_text': 'U2 I2 text'},
                            {'i_title': 'U2 Third title', 'i_text': 'U2 I3 text'}
                            ]

    def test_successful_create_and_get_idea(self):
        print('test_successful_create_and_get_idea-3')
        # ---------- set user1 auth
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user1))
        # ---------- create ideas for user 1
        for idea in self.user1_ideas:
            response = self.client.post(self.create_user_idea, {'new_idea': idea}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ---------- We want to make sure we have three ideas in the database..
        self.assertEqual(Idea.objects.count(), 3)

        # ---------- set user2 auth
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user2))
        # ---------- create ideas for user 2
        for idea in self.user2_ideas:
            response = self.client.post(self.create_user_idea, {'new_idea': idea}, format='json')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # ---------- We want to make sure we have six ideas in the database..
        self.assertEqual(Idea.objects.count(), 6)

        # ---------- ideas of both authors in the ideas list
        response = self.client.get(self.create_user_idea, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ---------- first user
        self.assertContains(response, 'http://testserver/api/v1/users/1/', status_code=status.HTTP_200_OK)
        # ---------- second user
        self.assertContains(response, 'http://testserver/api/v1/users/2/', status_code=status.HTTP_200_OK)

        # ---------- URL to update an idea or get detail view.
        idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 2})
        # ---------- get particular idea
        # ---------- we are using user2 auth
        response = self.client.get(idea_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ---------- we must get a dict with a key 'idea'
        self.assertIn('idea', response.data)

        idea_pattern = {'i_title': 'U1 Second title', 'i_text': 'U1 I2 text',
                        'author': 'http://testserver/api/v1/users/1/',
                        'likes_status': {'is_like': False, 'is_unlike': False, 'overall_likes': 0,
                                         'overall_unlikes': 0}}

        for key, value in idea_pattern.items():
            self.assertIn(key, response.data['idea'].keys())
            self.assertIn(value, response.data['idea'].values())

        idea_pattern_with_likes = {'i_title': 'U1 Second title', 'i_text': 'U1 I2 text',
                                   'author': 'http://testserver/api/v1/users/1/',
                                   'likes_status': {'is_like': True, 'is_unlike': False, 'overall_likes': 1,
                                                    'overall_unlikes': 0}}
        # ---------- nobody liked the idea at the moment
        self.assertNotIn(idea_pattern_with_likes['likes_status'], response.data['idea'].values())

    def test_unsuccessful_create_and_get_idea(self):
        print('test_unsuccessful_create_and_get_idea-4')
        # ---------- set no auth
        self.client.credentials()
        # ---------- create ideas
        for idea in self.user1_ideas:
            response = self.client.post(self.create_user_idea, {'new_idea': idea}, format='json')
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ---------- URL to update an idea or get detail view.
        idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 2})
        # ---------- get particular idea
        # ---------- we are using user2 auth
        response = self.client.get(idea_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ---------- set user2 auth
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user2))
        response = self.client.get(idea_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class IdeaLikingUpdateDeleteTest(APITestCase):
    def setUp(self):
        self.test_user1 = _usermodel.objects.create_user(username='testuser',
                                                         email='test@example.com',
                                                         password='Testpassword123',
                                                         is_active=True)
        self.test_user2 = _usermodel.objects.create_user(username='adminadmin',
                                                         email='ee2010@gmail.com',
                                                         password="PpPp123456",
                                                         is_active=True)
        self.test_user3 = _usermodel.objects.create_user(username='user3',
                                                         email='user3@gmail.com',
                                                         password="DdPp123456",
                                                         is_active=True)

        self.token_user1 = self.client.post(reverse('token_obtain_pair'),
                                            {'username': 'testuser', 'password': 'Testpassword123', },
                                            format='json').data['access']

        self.token_user2 = self.client.post(reverse('token_obtain_pair'),
                                            {'username': 'adminadmin', 'password': 'PpPp123456', },
                                            format='json').data['access']

        self.token_user3 = self.client.post(reverse('token_obtain_pair'),
                                            {'username': 'user3', 'password': 'DdPp123456', },
                                            format='json').data['access']

        users_ideas = [{'i_title': 'U1 First title', 'i_text': 'U1 I1 text', 'author': self.test_user1},
                       {'i_title': 'U1 Second title', 'i_text': 'U1 I2 text', 'author': self.test_user1},
                       {'i_title': 'U1 Third title', 'i_text': 'U1 I3 text', 'author': self.test_user1},
                       {'i_title': 'U2 First title', 'i_text': 'U2 I1 text', 'author': self.test_user2},
                       {'i_title': 'U2 Second title', 'i_text': 'U2 I2 text', 'author': self.test_user2},
                       {'i_title': 'U2 Third title', 'i_text': 'U2 I3 text', 'author': self.test_user2}
                       ]

        for i_object in users_ideas:
            Idea.objects.create(i_title=i_object['i_title'],
                                i_text=i_object['i_text'],
                                author=i_object['author']
                                )

    def test_successful_idea_liking(self):
        print('test_successful_idea_liking-5')
        # ---------- give likes to idea
        # ---------- create likes url
        add_likes_url = reverse('rest_api:likes-add', kwargs={'pk': 4})

        #  ---------- from user1
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user1))
        response = self.client.post(add_likes_url,
                                    {'likes_status': {'is_like': True, 'is_unlike': False, }},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ---------- from user3
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user3))
        response = self.client.post(add_likes_url,
                                    {'likes_status': {'is_like': False, 'is_unlike': True, }},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ---------- URL to  get detail view after we liked it.
        idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 4})
        # ---------- get particular idea
        # ---------- we are using user3 auth
        response = self.client.get(idea_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # ---------- we must get a dict with a key 'idea'
        self.assertIn('idea', response.data)

        idea_pattern = {'i_title': 'U2 First title', 'i_text': 'U2 I1 text',
                        'author': 'http://testserver/api/v1/users/2/',
                        'likes_status': {'is_like': False, 'is_unlike': True, 'overall_likes': 1,
                                         'overall_unlikes': 1}}

        for key, value in idea_pattern.items():
            self.assertIn(key, response.data['idea'].keys())
            self.assertIn(value, response.data['idea'].values())

        # ---------- we want to update idea id=4,  author = user2
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user2))

    def test_unsuccessful_idea_liking(self):
        print('test_unsuccessful_idea_liking-6')
        # ---------- give likes to idea
        # ---------- create likes url
        add_likes_url = reverse('rest_api:likes-add', kwargs={'pk': 400})

        # ---------- from user1
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user1))
        response = self.client.post(add_likes_url,
                                    {'likes_status': {'is_like': True, 'is_unlike': False, }},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        add_likes_url = reverse('rest_api:likes-add', kwargs={'pk': 4})
        response = self.client.post(add_likes_url,
                                    {'': ''},
                                    format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        idea_pattern = {'i_title': 'U2 First title', 'i_text': 'U2 I1 text',
                        'author': 'http://testserver/api/v1/users/2/',
                        'likes_status': {'is_like': False, 'is_unlike': False, 'overall_likes': 0,
                                         'overall_unlikes': 0}}

        idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 4})
        # ---------- get particular idea
        # ---------- we are using user2 auth
        response = self.client.get(idea_url, format='json')
        # ---------- test that nothing changed after wrong update data
        for key, value in idea_pattern.items():
            self.assertIn(key, response.data['idea'].keys())
            self.assertIn(value, response.data['idea'].values())

    def test_successful_idea_update(self):
        print('test_successful_idea_update-7')
        # ---------- update user1 idea id=3
        update_url = reverse('rest_api:idea-detail', kwargs={'pk': 3})

        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user1))
        response = self.client.put(update_url,
                                   {"updated_idea": {"i_title": "Updated", "i_text": "Updated"}},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # ---------- get particular idea
        # ---------- we are using user1 auth
        idea_pattern = {'i_title': 'Updated', 'i_text': 'Updated',
                        'author': 'http://testserver/api/v1/users/1/',
                        'likes_status': {'is_like': False, 'is_unlike': False, 'overall_likes': 0,
                                         'overall_unlikes': 0}}

        idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 3})
        # ---------- get particular idea
        # ---------- we are using user2 auth
        response = self.client.get(idea_url, format='json')
        # ---------- test that nothing changed after wrong update data
        for key, value in idea_pattern.items():
            self.assertIn(key, response.data['idea'].keys())
            self.assertIn(value, response.data['idea'].values())

    def test_unsuccessful_idea_update(self):
        print('test_unsuccessful_idea_update-8')
        # ---------- update user1 idea id=3
        update_url = reverse('rest_api:idea-detail', kwargs={'pk': 3})
        # set no auth
        self.client.credentials()
        response = self.client.put(update_url,
                                   {"updated_idea": {"i_title": "Updated", "i_text": "Updated", }},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # ---------- set user3 auth
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user3))
        response = self.client.put(update_url,
                                   {"updated_idea": {"i_title": "Updated", "i_text": "Updated", }},
                                   format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        idea_pattern = {'i_title': 'U1 Third title', 'i_text': 'U1 I3 text',
                        'author': 'http://testserver/api/v1/users/1/',
                        'likes_status': {'is_like': False, 'is_unlike': False, 'overall_likes': 0,
                                         'overall_unlikes': 0}}

        idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 3})
        # ---------- get particular idea
        # ---------- we are using user2 auth
        response = self.client.get(idea_url, format='json')

        # test that nothing changed after wrong update data
        for key, value in idea_pattern.items():
            self.assertIn(key, response.data['idea'].keys())
            self.assertIn(value, response.data['idea'].values())

    def test_successful_delete_idea(self):
        print('test_successful_delete_idea-9')
        # ---------- set user1 auth, which is author
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user1))

        # ---------- create delete url
        delete_idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 3})
        self.assertEqual(Idea.objects.count(), 6)
        response = self.client.delete(delete_idea_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Idea.objects.count(), 5)

    def test_unsuccessful_delete_idea(self):
        print('test_unsuccessful_delete_idea-10')
        # ---------- set user3 auth, which is not author
        self.client.credentials(HTTP_AUTHORIZATION="Bearer  {}".format(self.token_user3))

        # ---------- create url to delete idea with id=3
        delete_idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 3})
        # ---------- find count of ideas in db before deletion
        self.assertEqual(Idea.objects.count(), 6)
        response = self.client.delete(delete_idea_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # ---------- find count of ideas in db after deletion
        self.assertEqual(Idea.objects.count(), 6)

        # ---------- create url to delete nonexistent idea
        delete_idea_url = reverse('rest_api:idea-detail', kwargs={'pk': 300})
        # ---------- find count of ideas in db before deletion
        self.assertEqual(Idea.objects.count(), 6)
        response = self.client.delete(delete_idea_url, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

        # ---------- find count of ideas in db after deletion
        self.assertEqual(Idea.objects.count(), 6)

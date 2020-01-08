from django.shortcuts import render
from django.contrib.auth import get_user_model
from .serializers import FullCustomUserSerializer, ShortCustomUserSerializer, \
    IdeaSerializer, LikesSerializer, IdeasListSerializer, UserCreateSerializer, UserActivateSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from .permissions import IsIdeaOwner
from django.http import Http404
from rest_framework.generics import get_object_or_404
from rest_framework.status import HTTP_201_CREATED
from .email import mail_confirmation

from ideas_place.models import Idea, Likes

_usermodel = get_user_model()


# Create your views here.


class UserDetail(APIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def get_object(self, pk):
        try:
            return _usermodel.objects.get(pk=pk)
        except _usermodel.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        author = self.get_object(pk)
        if author == self.request.user:
            serializer = FullCustomUserSerializer(author, context={'request': self.request})
        else:
            serializer = ShortCustomUserSerializer(author, context={'request': self.request})

        return Response({'author': serializer.data})


class NewUserRegister(APIView):
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, format=None):
        new_user = request.data.get('new_user', None)
        serializer = UserCreateSerializer(data=new_user)

        if serializer.is_valid(raise_exception=True):
            saved_user = serializer.save(is_active=False, is_staff=False)
            mail_confirmation(user_=saved_user, request=request)

        return Response({'success': 'User {} created successfully.'.format(saved_user.username)}, status=HTTP_201_CREATED)


class NewUserActivate(APIView):
    permission_classes = [permissions.AllowAny, ]

    def post(self, request, format=None):
        # new_user = request.data.get('new_user', None)
        activation_data = request.data.get('activation', None)
        serializer = UserActivateSerializer(data=activation_data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        user.is_active = True
        user.save()

        return Response({'success': 'User {} successfully activated'.format(user.username)})


class IdeaTools(APIView):
    my_model = Idea
    permission_classes = [permissions.IsAuthenticated, IsIdeaOwner, ]

    def get_object(self, pk):
        try:
            return self.my_model.objects.get(pk=pk)
        except Idea.DoesNotExist:
            raise Http404

    def get(self, request, pk=None, format=None):
        if pk is not None:
            idea = self.get_object(pk)
            serializer = IdeaSerializer(idea, context={'request': self.request, 'current_user': request.user})
            return Response({'idea': serializer.data})
        else:
            all_ideas = self.my_model.objects.all()
            serializer = IdeasListSerializer(all_ideas, context={'request': self.request}, many=True)
            return Response({'all_ideas': serializer.data})

    def post(self, request, format=None):
        new_idea = request.data.get('new_idea', None)
        serializer = IdeaSerializer(data=new_idea, context={'request': self.request})
        if serializer.is_valid(raise_exception=True):
            idea_saved = serializer.save(author=request.user)
        return Response({'success': "The Idea {} saved".format(idea_saved.i_title)}, status=HTTP_201_CREATED)

    def put(self, request, pk):
        saved_idea = get_object_or_404(self.my_model.objects.all(), pk=pk)
        # check object permission
        self.check_object_permissions(self.request, saved_idea)
        updated_idea_data = request.data.get('updated_idea')
        serializer = IdeaSerializer(instance=saved_idea, data=updated_idea_data, partial=True)

        if serializer.is_valid(raise_exception=True):
            idea_saved = serializer.save()
        return Response({'success': 'The Idea {} updated successfully'.format(idea_saved.i_title)})

    def delete(self, request, pk):
        idea = get_object_or_404(self.my_model.objects.all(), pk=pk)
        # check object permission
        self.check_object_permissions(self.request, idea)
        idea.delete()
        return Response({'success': 'The Idea with id={} disappeared'.format(pk)})


class AddLikes(APIView):
    permission_classes = [permissions.IsAuthenticated, ]

    def post(self, request, format=None, **kwargs):

        parent_idea = self.kwargs.get('pk', None)
        user = request.user.id
        try:
            related_like = Likes.objects.get(parent_idea=parent_idea, user=user)
        except:
            related_like = None

        likes_status = request.data.get('likes_status', {})
        if related_like is not None:
            serializer = LikesSerializer(instance=related_like, data=likes_status, partial=True)
        else:
            likes_status.update({'parent_idea': parent_idea, 'user': user})
            serializer = LikesSerializer(data=likes_status)

        if serializer.is_valid(raise_exception=True):
            serializer.save()
        return Response({'success': "Likes status for idea`s id={} saved".format(parent_idea)})

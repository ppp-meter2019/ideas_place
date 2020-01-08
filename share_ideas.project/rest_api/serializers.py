from rest_framework import exceptions, serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from ideas_place.models import Idea, Likes
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions as django_exceptions
from django.db import IntegrityError
from django.utils.encoding import force_text
from .email import account_activation_token
from django.utils.http import urlsafe_base64_decode
from rest_framework.exceptions import ValidationError
from django.dispatch import Signal

_usermodel = get_user_model()


class FullCustomUserSerializer(serializers.ModelSerializer):
    ideas = serializers.HyperlinkedRelatedField(many=True, view_name='rest_api:user-detail', read_only=True)

    class Meta:
        model = _usermodel
        fields = ['username', 'email', 'ideas', ]


class ShortCustomUserSerializer(serializers.ModelSerializer):
    ideas = serializers.HyperlinkedRelatedField(many=True, view_name='rest_api:user-detail', read_only=True)

    class Meta:
        model = _usermodel
        fields = ['username', 'ideas', ]


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField()
    default_error_messages = {
        "cannot_create_user": "DB ERROR. Cannot create new user"
    }

    class Meta:
        model = _usermodel
        fields = ['username', 'email', 'password', 'first_name', 'last_name']
        extra_kwargs = {'password': {'write_only': True}, 'style': {"input_type": "password"}}

    def validate(self, attrs):
        user = _usermodel(**attrs)
        password = attrs.get("password")

        try:
            validate_password(password, user)
        except django_exceptions.ValidationError as e:
            serializer_error = serializers.as_serializer_error(e)
            raise serializers.ValidationError(
                {"password": serializer_error["non_field_errors"]}
            )

        return attrs

    def create(self, validated_data):
        try:
            user = _usermodel.objects.create_user(**validated_data)
        except IntegrityError:

            self.fail("cannot_create_user")

        return user


class UidTokenSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    default_error_messages = {
        "invalid_token": "Invalid activation Token",
        "invalid_uid": "Invalid user's UID ",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        confirmation = False
        try:
            uid = force_text(urlsafe_base64_decode(self.initial_data.get('uid', "")))
            self.user = _usermodel.objects.get(pk=uid)
        except (_usermodel.DoesNotExist, ValueError, TypeError, OverflowError):
            user = None
            key_error = "invalid_uid"
            raise ValidationError(
                {"uid": [self.error_messages[key_error]]}, code=key_error
            )

        is_token_valid = account_activation_token.check_token(self.user, self.initial_data.get('token', ""))
        if is_token_valid:
            return validated_data
        else:
            key_error = "invalid_token"
            raise ValidationError(
                {"token": [self.error_messages[key_error]]}, code=key_error
            )


class UserActivateSerializer(UidTokenSerializer):
    default_error_messages = {
        "stale_token": 'Given token is stale'
    }

    def validate(self, attrs):
        attrs = super().validate(attrs)
        if not self.user.is_active:
            return attrs
        raise exceptions.PermissionDenied(self.error_messages["stale_token"])


class LikesSerializer(serializers.ModelSerializer):
    overall_likes = serializers.IntegerField(read_only=True)
    overall_unlikes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Likes
        fields = ['parent_idea', 'user', 'is_like', 'is_unlike', 'overall_likes', 'overall_unlikes']
        extra_kwargs = {'parent_idea': {'write_only': True}, 'user': {'write_only': True}}

    # def validate(self, attrs):
    #     pass

    def create(self, validated_data):
        return Likes.objects.create(**validated_data)

    def update(self, instance, validate_data):
        instance.is_like = validate_data.get('is_like', instance.is_like)
        instance.is_unlike = validate_data.get('is_unlike', instance.is_unlike)
        instance.save()
        return instance


class IdeasListSerializer(serializers.HyperlinkedModelSerializer):
    author = serializers.HyperlinkedRelatedField(view_name='rest_api:user-detail', read_only=True)
    url = serializers.HyperlinkedIdentityField(view_name='rest_api:idea-detail', read_only=True, lookup_field='pk')

    class Meta:
        model = Idea
        fields = ['url', 'i_title', 'author', 'date_published']


class IdeaSerializer(serializers.ModelSerializer):
    author = serializers.HyperlinkedRelatedField(view_name='rest_api:user-detail', read_only=True)
    likes_status = serializers.SerializerMethodField()

    class Meta:
        model = Idea
        fields = ['i_title', 'i_text', 'author', 'date_published', 'likes_status']

    def create(self, validated_data):

        return Idea.objects.create(**validated_data)

    def update(self, instance, validate_data):
        instance.i_title = validate_data.get('i_title', instance.i_title)
        instance.i_text = validate_data.get('i_text', instance.i_text)
        instance.save()
        return instance

    def get_likes_status(self, obj):

        try:
            particular_users_likes = Likes.objects.get(user=self.context['current_user'], parent_idea=obj)
        except:
            particular_users_likes = Likes({'is_like': False, 'is_unlike': False})

        overall_likes_status = Likes.objects.filter(
            parent_idea=obj).aggregate(
            overall_likes=Count('is_like', filter=Q(is_like=True)),
            overall_unlikes=Count('is_unlike', filter=Q(is_unlike=True)))
        setattr(particular_users_likes, 'overall_likes', overall_likes_status['overall_likes'])
        setattr(particular_users_likes, 'overall_unlikes', overall_likes_status['overall_unlikes'])
        serializer = LikesSerializer(particular_users_likes)
        return serializer.data

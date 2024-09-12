from dj_rest_auth.views import LoginView
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin
from rest_framework.mixins import RetrieveModelMixin
from rest_framework.mixins import UpdateModelMixin
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from rest_framework_simplejwt.tokens import RefreshToken

from cryptotrackr.users.models import User

from .serializers import UserSerializer


class UserViewSet(RetrieveModelMixin, ListModelMixin, UpdateModelMixin, GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()
    lookup_field = "pk"

    def get_queryset(self, *args, **kwargs):
        assert isinstance(self.request.user.id, int)
        return self.queryset.filter(id=self.request.user.id)

    @action(detail=False)
    def me(self, request):
        serializer = UserSerializer(request.user, context={"request": request})
        return Response(status=status.HTTP_200_OK, data=serializer.data)


class CustomLoginView(LoginView):
    def get_response(self):
        original_response = super().get_response()
        user = self.user
        refresh = RefreshToken.for_user(user)
        original_response.data["access"] = str(refresh.access_token)
        original_response.data["refresh"] = str(refresh)
        original_response.data["full_name"] = user.name
        original_response.data["email"] = user.email
        if "key" in original_response.data:
            del original_response.data["key"]

        return original_response

from django.urls import path
from .views import RegisterView, LoginView, LogoutView, UserView, CSRFView, OperatorCreateView, OperatorListView, OperatorDeleteView,OrderView, FingerprintsView

from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("login/", LoginView.as_view()),
    path("logout/", LogoutView.as_view()),
    path("csrf/", CSRFView.as_view()),
    path("user/", UserView.as_view()),

    path("operators/", OperatorListView.as_view()),
    path("create-operator/", OperatorCreateView.as_view()),
    path("delete-operator/<int:pk>/", OperatorDeleteView.as_view()),

    path("orders/", OrderView.as_view()),
    path("orders/<int:pk>/", OrderView.as_view()),

    path("orders/<int:pk>/fingerprints/",FingerprintsView.as_view()),

]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
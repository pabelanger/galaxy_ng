from django.urls import path, include
from rest_framework import routers

from galaxy_ng.app import constants

from . import views
from . import viewsets


router = routers.SimpleRouter()
# TODO: Replace with a RedirectView
router.register('namespaces', viewsets.NamespaceViewSet, basename='namespaces')
router.register('my-namespaces', viewsets.MyNamespaceViewSet, basename='my-namespaces')
router.register('my-synclists', viewsets.MySyncListViewSet, basename='my-synclists')
router.register('collections', viewsets.CollectionViewSet, basename='collections')
router.register('users', viewsets.UserViewSet, basename='users')
router.register('collection-versions',
                viewsets.CollectionVersionViewSet, basename='collection-versions')
router.register(
    'imports/collections',
    viewsets.CollectionImportViewSet,
    basename='collection-imports',
)
router.register('tags', viewsets.TagsViewSet, basename='tags')
router.register('synclists', viewsets.SyncListViewSet, basename='synclists')

auth_views = [
    path("login/", views.LoginView.as_view(), name="auth-login"),
    path("logout/", views.LogoutView.as_view(), name="auth-logout"),
]

paths = [
    path('', include(router.urls)),

    path('auth/', include(auth_views)),

    # NOTE: Using path instead of SimpleRouter because SimpleRouter expects retrieve
    # to look up values with an ID
    path(
        'me/',
        viewsets.CurrentUserViewSet.as_view({'get': 'retrieve', 'put': 'update'}),
        name='me'
    )
]
app_name = "ui"

urlpatterns = [
    path('', viewsets.APIRootView.as_view({'get': 'list'}))
]

for version in constants.ALL_UI_API_VERSION:
    urlpatterns.append(path(
        constants.ALL_UI_API_VERSION[version],
        include((paths, app_name), namespace=version)
    ))

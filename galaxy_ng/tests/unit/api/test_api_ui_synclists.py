import logging

from rest_framework import status as http_code

from guardian import shortcuts

from galaxy_ng.app.models import auth as auth_models

from . import base
from .synclist_base import BaseSyncListViewSet, ACCOUNT_SCOPE

log = logging.getLogger(__name__)


class TestUiSynclistViewSet(BaseSyncListViewSet):
    """Test SyncListViewSet as an admin / pe_group member"""

    def setUp(self):
        super().setUp()
        self.user = auth_models.User.objects.create(username="admin")
        self.group = self._create_partner_engineer_group()
        self.user.groups.add(self.group)
        self.user.save()

        self.synclist_name = "test_synclist"
        self.synclist = self._create_synclist(
            name=self.synclist_name,
            repository=self.repo,
            upstream_repository=self.default_repo,
            groups=[self.group],
        )

        self.synclist.save()

        self.client.force_authenticate(user=self.user)

    def _group(self, user_group, perms=None):
        perms = perms or self.default_owner_permissions
        group = {
            "id": user_group.id,
            "name": user_group.name,
            "object_permissions": perms,
        }
        return group

    def test_synclist_create(self):
        post_data = {
            "repository": self.repo.pulp_id,
            "collections": [],
            "namespaces": [],
            "policy": "include",
            "name": self.synclist_name,
            "groups": [self._group(self.group)],
        }

        synclists_url = base.get_current_ui_url("synclists-list")

        response = self.client.post(synclists_url, post_data, format="json")

        log.debug("response: %s", response)
        log.debug("response.data: %s", response.data)

        self.assertEqual(response.status_code, http_code.HTTP_201_CREATED, msg=response.data)

    def test_synclist_update(self):
        ns1_name = "unittestnamespace1"
        ns2_name = "unittestnamespace2"
        ns1 = self._create_namespace(ns1_name, groups=[self.group])
        ns2 = self._create_namespace(ns2_name, groups=[self.group])
        ns1.save()
        ns2.save()

        post_data = {
            "repository": self.repo.pulp_id,
            "collections": [],
            "namespaces": [ns1_name, ns2_name],
            "policy": "include",
            "groups": [self._group(self.group)],
        }

        synclists_detail_url = base.get_current_ui_url(
            "synclists-detail", kwargs={"pk": self.synclist.id}
        )

        response = self.client.patch(synclists_detail_url, post_data, format="json")

        log.debug("response: %s", response)
        log.debug("response.data: %s", response.data)

        self.assertEqual(response.status_code, http_code.HTTP_200_OK, msg=response.data)
        self.assertIn("name", response.data)
        self.assertIn("repository", response.data)
        self.assertEqual(response.data["name"], self.synclist_name)
        self.assertEqual(response.data["policy"], "include")

    def test_synclist_list(self):
        synclists_url = base.get_current_ui_url("synclists-list")
        response = self.client.get(synclists_url)

        log.debug("response.data: %s", response.data)

        self.assertEqual(response.status_code, http_code.HTTP_200_OK, msg=response.data)

    def test_synclist_list_empty(self):
        synclists_url = base.get_current_ui_url("synclists-list")

        response = self.client.get(synclists_url)

        log.debug("response: %s", response)
        log.debug("data: %s", response.data)

        self.assertEqual(response.status_code, http_code.HTTP_200_OK, msg=response.data)

    def test_synclist_detail(self):
        synclists_detail_url = base.get_current_ui_url(
            "synclists-detail", kwargs={"pk": self.synclist.id}
        )

        response = self.client.get(synclists_detail_url)

        self.assertEqual(response.status_code, http_code.HTTP_200_OK, msg=response.data)
        self.assertIn("name", response.data)
        self.assertIn("repository", response.data)
        self.assertEqual(response.data["name"], self.synclist_name)
        self.assertEqual(response.data["policy"], "exclude")
        self.assertEqual(response.data["collections"], [])
        self.assertEqual(response.data["namespaces"], [])

    def test_synclist_delete(self):
        synclists_detail_url = base.get_current_ui_url(
            "synclists-detail", kwargs={"pk": self.synclist.id}
        )

        log.debug("delete url: %s", synclists_detail_url)

        response = self.client.delete(synclists_detail_url)

        log.debug("delete response: %s", response)

        self.assertEqual(response.status_code, http_code.HTTP_204_NO_CONTENT, msg=response.data)


class TestUiSynclistViewSetRegularUser(TestUiSynclistViewSet):
    def setUp(self):
        super().setUp()

        self.user = auth_models.User.objects.create_user(username="test1", password="test1-secret")
        self.group = self._create_group_with_synclist_perms(
            ACCOUNT_SCOPE, "test1_group", users=[self.user]
        )
        self.user.save()
        self.group.save()

        self.user.groups.add(self.group)
        self.user.save()

        self.synclist_name = "test_synclist"
        self.synclist = self._create_synclist(
            name=self.synclist_name,
            repository=self.repo,
            upstream_repository=self.default_repo,
            groups=[self.group],
        )

        self.client.force_authenticate(user=self.user)


class TestUiSynclistViewSetNoGroupPerms(TestUiSynclistViewSet):
    def setUp(self):
        super().setUp()

        self.user = auth_models.User.objects.create_user(
            username="test_user_noperms", password="test1-secret"
        )
        self.group = self._create_group(ACCOUNT_SCOPE, "test_group_no_perms", users=[self.user])
        self.user.save()
        self.group.save()

        for perm in self.default_owner_permissions:
            shortcuts.remove_perm(f"galaxy.{perm}", self.group)
        self.group.save()

        self.synclist_name = "test_synclist"
        self.synclist = self._create_synclist(
            name=self.synclist_name, repository=self.repo, upstream_repository=self.default_repo,
        )

        self.client.force_authenticate(user=self.user)

    def test_synclist_create(self):
        post_data = {
            "repository": self.repo.pulp_id,
            "collections": [],
            "namespaces": [],
            "policy": "include",
            "name": self.synclist_name,
            "groups": [self._group(self.group)],
        }

        synclists_url = base.get_current_ui_url("synclists-list")
        response = self.client.post(synclists_url, post_data, format="json")
        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

    def test_synclist_detail(self):
        synclists_detail_url = base.get_current_ui_url(
            "synclists-detail", kwargs={"pk": self.synclist.id}
        )

        response = self.client.get(synclists_detail_url)
        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

    def test_synclist_list(self):
        synclists_url = base.get_current_ui_url("synclists-list")
        response = self.client.get(synclists_url)
        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

    def test_synclist_list_empty(self):
        synclists_url = base.get_current_ui_url("synclists-list")
        response = self.client.get(synclists_url)
        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

    def test_synclist_update(self):
        post_data = {
            "repository": self.repo.pulp_id,
            "collections": [],
            "namespaces": [],
            "policy": "include",
            "groups": [self._group(self.group)],
        }

        synclists_detail_url = base.get_current_ui_url(
            "synclists-detail", kwargs={"pk": self.synclist.id}
        )

        response = self.client.patch(synclists_detail_url, post_data, format="json")

        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

    def test_synclist_delete(self):
        synclists_detail_url = base.get_current_ui_url(
            "synclists-detail", kwargs={"pk": self.synclist.id}
        )

        response = self.client.delete(synclists_detail_url)
        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

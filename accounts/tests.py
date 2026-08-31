"""accounts/tests.py"""

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from nvr.models import Camera


class AccountsRegistrationTests(TestCase):
    def test_registration_page_renders(self):
        response = self.client.get(reverse("accounts:register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertContains(response, "Create an account")
        self.assertContains(response, "Work Email")

    def test_user_registration_success_provisions_camera_and_profile(self):
        post_data = {
            "username": "charlie_guard",
            "email": "charlie@company.com",
            "password": "SecurePassword123",
            "password_confirm": "SecurePassword123",
        }
        response = self.client.post(reverse("accounts:register"), post_data)
        # Should redirect to live
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("nvr:live"))

        # Verify user created
        user = User.objects.get(username="charlie_guard")
        self.assertEqual(user.email, "charlie@company.com")

        # Verify default camera provisioned
        self.assertTrue(Camera.objects.filter(owner=user).exists())

        # Verify default service profile created
        self.assertTrue(hasattr(user, "service_profile"))
        self.assertTrue(user.service_profile.has_vehicles_people)
        self.assertFalse(user.service_profile.has_face_recognition)

    def test_registration_password_mismatch_fails(self):
        post_data = {
            "username": "david",
            "email": "david@company.com",
            "password": "Password123",
            "password_confirm": "WrongPassword123",
        }
        response = self.client.post(reverse("accounts:register"), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Passwords do not match")
        self.assertFalse(User.objects.filter(username="david").exists())

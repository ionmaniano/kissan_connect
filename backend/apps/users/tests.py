from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class AuthenticationTests(APITestCase):
    def setUp(self):
        self.register_url = reverse("user-register")
        self.token_url = reverse("token-obtain-pair")
        self.refresh_url = reverse("token-refresh")
        self.logout_url = reverse("user-logout")
        self.me_url = reverse("user-me")

        self.farmer_data = {
            "username": "farmer_ali",
            "email": "ali@example.com",
            "password": "SecurePassword123!",
            "role": "FARMER",
        }

        self.buyer_data = {
            "username": "buyer_sara",
            "email": "sara@example.com",
            "password": "SecurePassword123!",
            "role": "BUYER",
        }

    # ============================================================
    # REGISTRATION TESTS
    # ============================================================

    def test_register_farmer_success(self):
        response = self.client.post(self.register_url, self.farmer_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["username"], "farmer_ali")
        self.assertEqual(response.data["role"], "FARMER")
        self.assertNotIn("password", response.data)
        self.assertTrue(User.objects.filter(username="farmer_ali").exists())

    def test_register_buyer_success(self):
        response = self.client.post(self.register_url, self.buyer_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["role"], "BUYER")

    def test_register_duplicate_username_fails(self):
        self.client.post(self.register_url, self.farmer_data)
        response = self.client.post(self.register_url, self.farmer_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_short_password_fails(self):
        invalid_data = self.farmer_data.copy()
        invalid_data["password"] = "short"
        response = self.client.post(self.register_url, invalid_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ============================================================
    # LOGIN / TOKEN TESTS
    # ============================================================

    def test_login_success(self):
        self.client.post(self.register_url, self.farmer_data)
        response = self.client.post(
            self.token_url,
            {
                "username": self.farmer_data["username"],
                "password": self.farmer_data["password"],
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_invalid_password_fails(self):
        self.client.post(self.register_url, self.farmer_data)
        response = self.client.post(
            self.token_url,
            {
                "username": self.farmer_data["username"],
                "password": "WrongPassword123!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh_success(self):
        self.client.post(self.register_url, self.farmer_data)
        login_res = self.client.post(
            self.token_url,
            {
                "username": self.farmer_data["username"],
                "password": self.farmer_data["password"],
            },
        )
        refresh_token = login_res.data["refresh"]

        refresh_res = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
        )
        self.assertEqual(refresh_res.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_res.data)

    # ============================================================
    # CURRENT USER (/me/) TESTS
    # ============================================================

    def test_me_authenticated_success(self):
        self.client.post(self.register_url, self.farmer_data)
        login_res = self.client.post(
            self.token_url,
            {
                "username": self.farmer_data["username"],
                "password": self.farmer_data["password"],
            },
        )
        access_token = login_res.data["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "farmer_ali")
        self.assertEqual(response.data["role"], "FARMER")

    def test_me_unauthenticated_fails(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ============================================================
    # LOGOUT & BLACKLIST TESTS
    # ============================================================

    def test_logout_blacklists_token(self):
        self.client.post(self.register_url, self.farmer_data)
        login_res = self.client.post(
            self.token_url,
            {
                "username": self.farmer_data["username"],
                "password": self.farmer_data["password"],
            },
        )
        access_token = login_res.data["access"]
        refresh_token = login_res.data["refresh"]

        # Logout with access token + refresh token in payload
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        logout_res = self.client.post(
            self.logout_url,
            {"refresh": refresh_token},
        )
        self.assertEqual(logout_res.status_code, status.HTTP_200_OK)

        # Attempting to refresh with the blacklisted token must fail
        refresh_res = self.client.post(
            self.refresh_url,
            {"refresh": refresh_token},
        )
        self.assertEqual(refresh_res.status_code, status.HTTP_401_UNAUTHORIZED)

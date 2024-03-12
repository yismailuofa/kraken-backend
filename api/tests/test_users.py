from unittest.mock import Mock

from fastapi import status

from api.schemas import User
from api.tests.util import TestBase


class TestUsers(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testUser = User(
            username="test",
            password="test",
            email="test@test.com",
        )

        cls.mockDb.users.insert_one = Mock(wraps=cls.mockDb.users.insert_one)
        cls.mockDb.users.find_one_and_update = Mock(
            wraps=cls.mockDb.users.find_one_and_update
        )
        cls.mockDb.users.find_one = Mock(wraps=cls.mockDb.users.find_one)

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})

        opts = {
            "return_value": True,
            "side_effect": True,
        }
        self.mockDb.users.insert_one.reset_mock(**opts)
        self.mockDb.users.find_one_and_update.reset_mock(**opts)
        self.mockDb.users.find_one.reset_mock(**opts)

    def registerUser(self):
        return self.client.post(
            "/users/register",
            json={
                "username": self.testUser.username,
                "password": self.testUser.password,
                "email": self.testUser.email,
            },
        )

    def loginUser(self):
        return self.client.post(
            "/users/login",
            params={
                "username": self.testUser.username,
                "password": self.testUser.password,
            },
        )

    def testRegister(self):
        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        json = response.json()

        self.assertEqual(json["username"], "test")
        self.assertNotEqual(json["password"], self.testUser.password)

        for v in json.values():
            self.assertIsNotNone(v)

    def testRegisterInvalid(self):
        response = self.client.post(
            "/users/register",
            json={
                "username": self.testUser.username,
                "password": self.testUser.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)

    def testRegisterInsertFailed(self):
        self.mockDb.users.insert_one.return_value.acknowledged = False

        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def testRegisterTokenFailed(self):
        self.mockDb.users.find_one_and_update.return_value = None

        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def testRegisterExisting(self):
        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def testRegisterExistingEmail(self):
        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            "/users/register",
            json={
                "username": self.testUser.username + "foo",
                "password": self.testUser.password,
                "email": self.testUser.email,
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def testLogin(self):
        registerResponse = self.registerUser()
        self.assertEqual(registerResponse.status_code, status.HTTP_201_CREATED)

        response = self.loginUser()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertDictEqual(response.json(), registerResponse.json())

    def testLoginInvalidPwd(self):
        response = self.client.post(
            "/users/login",
            params={
                "username": self.testUser.username,
                "password": self.testUser.password + "foo",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testLoginInvalidUser(self):
        response = self.client.post(
            "/users/login",
            params={
                "username": self.testUser.username + "foo",
                "password": self.testUser.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetCurrentUser(self):
        registerResponse = self.registerUser()
        self.assertEqual(registerResponse.status_code, status.HTTP_201_CREATED)

        response = self.loginUser()
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        token = response.json()["token"]

        response = self.client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json = response.json()

        self.assertDictEqual(json, registerResponse.json())

    def testGetCurrentUserInvalid(self):
        response = self.client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalidtoken"},
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def testGetCurrentUserNotFound(self):
        response = self.registerUser()
        token = response.json()["token"]

        self.mockDb.users.find_one.return_value = None

        response = self.client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def testChangePassword(self):
        registerResponse = self.registerUser()
        self.assertEqual(registerResponse.status_code, status.HTTP_201_CREATED)

        token = registerResponse.json()["token"]

        response = self.client.patch(
            "/users/password/reset",
            headers={"Authorization": f"Bearer {token}"},
            params={"newPassword": "newpassword"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            "/users/login",
            params={
                "username": self.testUser.username,
                "password": "newpassword",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def testChangePasswordFailure(self):
        registerResponse = self.registerUser()
        token = registerResponse.json()["token"]

        self.mockDb.users.find_one_and_update.return_value = None

        response = self.client.patch(
            "/users/password/reset",
            headers={"Authorization": f"Bearer {token}"},
            params={"newPassword": "newpassword"},
        )

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

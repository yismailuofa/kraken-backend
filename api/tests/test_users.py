import unittest

from fastapi import status
from fastapi.testclient import TestClient
from mongomock import MongoClient

from api.database import getDb
from api.main import app
from api.schemas import User


class TestUsers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.testUser = User(
            username="test",
            password="test",
            email="test@test.com",
        )
        cls.mockDb = MongoClient().db
        app.dependency_overrides[getDb] = lambda: cls.mockDb

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})

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

    def testRegisterExisting(self):
        response = self.registerUser()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.registerUser()
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

    def testChangePassword(self):
        registerResponse = self.registerUser()
        self.assertEqual(registerResponse.status_code, status.HTTP_201_CREATED)

        token = registerResponse.json()["token"]

        response = self.client.put(
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


if __name__ == "__main__":
    unittest.main()

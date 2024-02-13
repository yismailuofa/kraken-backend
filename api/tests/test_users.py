import unittest

from fastapi import status
from fastapi.testclient import TestClient

from api.main import app
from api.schemas import User


class TestUsers(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.testUser = User(
            username="test",
            password="test",
            email="test@test.com",
        )

    def testRegister(self):
        response = self.client.post(
            "/users/register",
            json={
                "username": self.testUser.username,
                "password": self.testUser.password,
                "email": self.testUser.email,
            },
        )
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

    def testLogin(self):
        response = self.client.post(
            "/users/register",
            json={
                "username": self.testUser.username,
                "password": self.testUser.password,
                "email": self.testUser.email,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        response = self.client.post(
            "/users/login",
            params={
                "username": self.testUser.username,
                "password": self.testUser.password,
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json = response.json()

        self.assertEqual(json["username"], "test")

        for v in json.values():
            self.assertIsNotNone(v)

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


if __name__ == "__main__":
    unittest.main()

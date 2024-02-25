import datetime

from fastapi import status

from api.schemas import UserView
from api.tests.util import TestBase


class TestProjects(TestBase):
    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})

    def testCreateProject(self):
        projectName = "test"
        projectDescription = "test"
        user = self.createUser("test")

        response = self.createProject(user, projectName, projectDescription)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        json = response.json()

        self.assertEqual(json["name"], projectName)
        self.assertEqual(json["description"], projectDescription)

        for v in json.values():
            self.assertIsNotNone(v)

        # check that the time is within 1 minute of the current time
        difference = datetime.datetime.now() - datetime.datetime.fromisoformat(
            json["createdAt"]
        )
        self.assertLessEqual(
            difference,
            datetime.timedelta(minutes=1),
        )

    def testGetProjects(self):
        user = self.createUser("test")

        getResponse = self.client.get("/projects/", headers=self.userToHeader(user))

        self.assertEqual(getResponse.status_code, status.HTTP_200_OK)
        self.assertEqual(getResponse.json(), [])

        createResponse = self.createProject(user, "test", "test")
        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        newGetResponse = self.client.get("/projects/", headers=self.userToHeader(user))
        self.assertEqual(newGetResponse.status_code, status.HTTP_200_OK)

        json = newGetResponse.json()
        self.assertEqual(len(json), 1)
        self.assertDictEqual(createResponse.json(), json[0])

    def testGetProject(self):
        user = self.createUser("test")

        projectName = projectDescription = "test"

        createResponse = self.createProject(user, projectName, projectDescription)

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        milestone = self.createMilestone(
            user, projectId, "test", "test", "2022-01-01T00:00:00"
        ).json()
        task = self.createTask(
            user,
            projectId,
            milestone["id"],
            "test",
            "test",
            "2022-01-01T00:00:00",
            {
                "name": "qatest",
                "description": "qatest",
                "dueDate": "2022-01-01T00:00:00",
            },
        ).json()

        sprint = self.createSprint(
            user,
            projectId,
            "test",
            "test",
            "2022-01-01T00:00:00",
            "2022-01-01T00:00:00",
        ).json()

        getResponse = self.client.get(
            f"/projects/{projectId}", headers=self.userToHeader(user)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_200_OK)

        self.assertEqual(getResponse.json()["id"], projectId)
        self.assertEqual(getResponse.json()["name"], projectName)
        self.assertEqual(getResponse.json()["description"], projectDescription)

        self.assertEqual(len(getResponse.json()["milestones"]), 1)
        self.assertDictEqual(getResponse.json()["milestones"][0], milestone)

        self.assertEqual(len(getResponse.json()["tasks"]), 1)
        self.assertDictEqual(getResponse.json()["tasks"][0], task)

        self.assertEqual(len(getResponse.json()["sprints"]), 1)
        self.assertDictEqual(getResponse.json()["sprints"][0], sprint)

    def testGetProjectForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        getResponse = self.client.get(
            f"/projects/{projectId}", headers=self.userToHeader(user2)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateProject(self):
        user = self.createUser("test")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        newName, newDescription = "newName", "newDescription"
        updateResponse = self.client.patch(
            f"/projects/{projectId}",
            json={"name": newName, "description": newDescription},
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateResponse.status_code, status.HTTP_200_OK)

        json = updateResponse.json()
        self.assertEqual(json["name"], newName)
        self.assertEqual(json["description"], newDescription)

    def testUpdateProjectForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        newName, newDescription = "newName", "newDescription"
        updateResponse = self.client.patch(
            f"/projects/{projectId}",
            json={"name": newName, "description": newDescription},
            headers=self.userToHeader(user2),
        )

        self.assertEqual(updateResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testJoinProject(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        joinResponse = self.client.post(
            f"/projects/{projectId}/join", headers=self.userToHeader(user2)
        )

        self.assertEqual(joinResponse.status_code, status.HTTP_200_OK)

        userResponse = self.client.get("/users/me", headers=self.userToHeader(user2))

        self.assertEqual(userResponse.status_code, status.HTTP_200_OK)
        self.assertEqual(userResponse.json()["joinedProjects"], [projectId])

    def testLeaveProject(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        joinResponse = self.client.post(
            f"/projects/{projectId}/join", headers=self.userToHeader(user2)
        )

        self.assertEqual(joinResponse.status_code, status.HTTP_200_OK)

        leaveResponse = self.client.delete(
            f"/projects/{projectId}/leave", headers=self.userToHeader(user2)
        )

        self.assertEqual(leaveResponse.status_code, status.HTTP_200_OK)

        userResponse = self.client.get("/users/me", headers=self.userToHeader(user2))

        self.assertEqual(userResponse.status_code, status.HTTP_200_OK)
        self.assertEqual(userResponse.json()["joinedProjects"], [])

    def testAddProjectUser(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        addUserResponse = self.client.post(
            f"/projects/{projectId}/users",
            headers=self.userToHeader(user),
            params={"email": user2["email"]},
        )

        self.assertEqual(addUserResponse.status_code, status.HTTP_200_OK)

        userResponse = self.client.get("/users/me", headers=self.userToHeader(user2))

        self.assertEqual(userResponse.status_code, status.HTTP_200_OK)
        self.assertEqual(userResponse.json()["joinedProjects"], [projectId])

    def testAddProjectUserForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")
        user3 = self.createUser("test3")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        addUserResponse = self.client.post(
            f"/projects/{projectId}/users",
            headers=self.userToHeader(user2),
            params={"email": user3["email"]},
        )

        self.assertEqual(addUserResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testRemoveProjectUser(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        addUserResponse = self.client.post(
            f"/projects/{projectId}/users",
            headers=self.userToHeader(user),
            params={"email": user2["email"]},
        )

        self.assertEqual(addUserResponse.status_code, status.HTTP_200_OK)

        removeUserResponse = self.client.delete(
            f"/projects/{projectId}/users",
            headers=self.userToHeader(user),
            params={"userID": user2["id"]},
        )

        self.assertEqual(removeUserResponse.status_code, status.HTTP_200_OK)

        userResponse = self.client.get("/users/me", headers=self.userToHeader(user2))

        self.assertEqual(userResponse.status_code, status.HTTP_200_OK)
        self.assertEqual(userResponse.json()["joinedProjects"], [])

    def testRemoveProjectUserForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        removeUserResponse = self.client.delete(
            f"/projects/{projectId}/users",
            headers=self.userToHeader(user2),
            params={"userID": user["id"]},
        )

        self.assertEqual(removeUserResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testGetProjectUsers(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        self.assertEqual(createResponse.status_code, status.HTTP_200_OK)

        projectId = createResponse.json()["id"]

        addUserResponse = self.client.post(
            f"/projects/{projectId}/users",
            headers=self.userToHeader(user),
            params={"email": user2["email"]},
        )

        self.assertEqual(addUserResponse.status_code, status.HTTP_200_OK)

        getResponse = self.client.get(
            f"/projects/{projectId}/users", headers=self.userToHeader(user)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_200_OK)
        self.assertListEqual(getResponse.json(), [UserView(**user2).model_dump()])

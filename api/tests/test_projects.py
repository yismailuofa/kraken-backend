import datetime
from unittest.mock import Mock

from bson import ObjectId
from fastapi import status

from api.schemas import UserView
from api.tests.util import TestBase


class TestProjects(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.mockDb.projects.insert_one = Mock(wraps=cls.mockDb.projects.insert_one)
        cls.mockDb.projects.delete_one = Mock(wraps=cls.mockDb.projects.delete_one)
        cls.mockDb.projects.find_one_and_update = Mock(
            wraps=cls.mockDb.projects.find_one_and_update
        )
        cls.mockDb.projects.find_one = Mock(wraps=cls.mockDb.projects.find_one)
        cls.mockDb.milestones.delete_many = Mock(
            wraps=cls.mockDb.milestones.delete_many
        )
        cls.mockDb.tasks.delete_many = Mock(wraps=cls.mockDb.tasks.delete_many)
        cls.mockDb.sprints.delete_many = Mock(wraps=cls.mockDb.sprints.delete_many)

        cls.mockDb.users.find_one_and_update = Mock(
            wraps=cls.mockDb.users.find_one_and_update
        )
        cls.mockDb.users.update_many = Mock(wraps=cls.mockDb.users.update_many)

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})

        opts = {
            "return_value": True,
            "side_effect": True,
        }
        self.mockDb.projects.insert_one.reset_mock(**opts)
        self.mockDb.projects.delete_one.reset_mock(**opts)
        self.mockDb.projects.find_one_and_update.reset_mock(**opts)
        self.mockDb.projects.find_one.reset_mock(**opts)

        self.mockDb.milestones.delete_many.reset_mock(**opts)
        self.mockDb.tasks.delete_many.reset_mock(**opts)
        self.mockDb.sprints.delete_many.reset_mock(**opts)

        self.mockDb.users.find_one_and_update.reset_mock(**opts)
        self.mockDb.users.update_many.reset_mock(**opts)

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

    def testCreateProjectFailure(self):
        user = self.createUser("test")

        self.mockDb.projects.insert_one.return_value.acknowledged = False

        response = self.createProject(user, "", "test")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def testCreateProjectUserFailure(self):
        user = self.createUser("test")

        self.mockDb.users.find_one_and_update.return_value = None

        response = self.createProject(user, "test", "test")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    def testDeleteProject(self):
        user = self.createUser("test")

        createResponse = self.createProject(user, "test", "test")

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

        deleteResponse = self.client.delete(
            f"/projects/{projectId}", headers=self.userToHeader(user)
        )

        self.assertEqual(deleteResponse.status_code, status.HTTP_200_OK)

        getResponse = self.client.get(
            f"/projects/{projectId}", headers=self.userToHeader(user)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_404_NOT_FOUND)

        getMilestoneResponse = self.client.get(
            f"/milestones/{milestone['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getMilestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

        getTaskResponse = self.client.get(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getTaskResponse.status_code, status.HTTP_404_NOT_FOUND)

        getSprintResponse = self.client.get(
            f"/sprints/{sprint['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getSprintResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testDeleteProjectNotFound(self):
        user = self.createUser("test")

        deleteResponse = self.client.delete(
            f"/projects/{ObjectId()}", headers=self.userToHeader(user)
        )

        self.assertEqual(deleteResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testDeleteProjectForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        projectId = createResponse.json()["id"]

        deleteResponse = self.client.delete(
            f"/projects/{projectId}", headers=self.userToHeader(user2)
        )

        self.assertEqual(deleteResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testDeleteProjectFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.projects.delete_one.return_value.acknowledged = False

        deleteResponse = self.client.delete(
            f"/projects/{project.json()['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteProjectMillstonesFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.milestones.delete_many.return_value.acknowledged = False

        deleteResponse = self.client.delete(
            f"/projects/{project.json()['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteProjectTasksFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.tasks.delete_many.return_value.acknowledged = False

        deleteResponse = self.client.delete(
            f"/projects/{project.json()['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteProjectSprintsFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.sprints.delete_many.return_value.acknowledged = False

        deleteResponse = self.client.delete(
            f"/projects/{project.json()['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteProjectUserFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.users.find_one_and_update.return_value = None

        deleteResponse = self.client.delete(
            f"/projects/{project.json()['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteProjectUserUpdateFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.users.update_many.return_value.acknowledged = False

        deleteResponse = self.client.delete(
            f"/projects/{project.json()['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

    def testUpdateProjectNotFound(self):
        user = self.createUser("test")

        updateResponse = self.client.patch(
            f"/projects/{ObjectId()}",
            headers=self.userToHeader(user),
            json={"name": "test", "description": "test"},
        )

        self.assertEqual(updateResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testUpdateProjectFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test")

        self.mockDb.projects.find_one_and_update.return_value = None

        updateResponse = self.client.patch(
            f"/projects/{project.json()['id']}",
            headers=self.userToHeader(user),
            json={"name": "test", "description": "test"},
        )

        self.assertEqual(
            updateResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

    def testJoinProjectNotFound(self):
        user = self.createUser("test")

        joinResponse = self.client.post(
            f"/projects/{ObjectId()}/join", headers=self.userToHeader(user)
        )

        self.assertEqual(joinResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testJoinProjectFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test")

        self.mockDb.users.find_one_and_update.return_value = None

        joinResponse = self.client.post(
            f"/projects/{project.json()['id']}/join", headers=self.userToHeader(user)
        )

        self.assertEqual(
            joinResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

    def testLeaveProjectNotFound(self):
        user = self.createUser("test")

        leaveResponse = self.client.delete(
            f"/projects/{ObjectId()}/leave", headers=self.userToHeader(user)
        )

        self.assertEqual(leaveResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testLeaveProjectFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test")

        self.mockDb.users.find_one_and_update.return_value = None

        leaveResponse = self.client.delete(
            f"/projects/{project.json()['id']}/leave", headers=self.userToHeader(user)
        )

        self.assertEqual(
            leaveResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

    def testAddProjectUserNotFound(self):
        user = self.createUser("test")

        addUserResponse = self.client.post(
            f"/projects/{ObjectId()}/users",
            headers=self.userToHeader(user),
            params={"email": "test"},
        )

        self.assertEqual(addUserResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testAddProjectUserFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test")

        self.mockDb.users.find_one_and_update.return_value = None

        addUserResponse = self.client.post(
            f"/projects/{project.json()['id']}/users",
            headers=self.userToHeader(user),
            params={"email": "test"},
        )

        self.assertEqual(
            addUserResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

    def testRemoveProjectUserNotFound(self):
        user = self.createUser("test")

        removeUserResponse = self.client.delete(
            f"/projects/{ObjectId()}/users",
            headers=self.userToHeader(user),
            params={"userID": "test"},
        )

        self.assertEqual(removeUserResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testRemoveProjectUserFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test")

        self.mockDb.users.find_one_and_update.return_value = None

        removeUserResponse = self.client.delete(
            f"/projects/{project.json()['id']}/users",
            headers=self.userToHeader(user),
            params={"userID": str(ObjectId())},
        )

        self.assertEqual(
            removeUserResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

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

    def testGetProjectUsersNotFound(self):
        user = self.createUser("test")

        getResponse = self.client.get(
            f"/projects/{ObjectId()}/users", headers=self.userToHeader(user)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testGetProjectUsersForbidden(self):
        user = self.createUser("test")
        user2 = self.createUser("test2")

        createResponse = self.createProject(user, "test", "test")

        projectId = createResponse.json()["id"]

        getResponse = self.client.get(
            f"/projects/{projectId}/users", headers=self.userToHeader(user2)
        )

        self.assertEqual(getResponse.status_code, status.HTTP_403_FORBIDDEN)

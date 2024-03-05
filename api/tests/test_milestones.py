from unittest.mock import Mock

from bson import ObjectId
from fastapi import status

from api.tests.util import TestBase


class TestMilestones(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.testMilestone = {
            "name": "test",
            "description": "test",
            "dueDate": "2001-10-01T00:00:00",
        }

        cls.mockDb.milestones.insert_one = Mock(wraps=cls.mockDb.milestones.insert_one)
        cls.mockDb.milestones.find_one_and_update = Mock(
            wraps=cls.mockDb.milestones.find_one_and_update
        )
        cls.mockDb.milestones.find_one = Mock(wraps=cls.mockDb.milestones.find_one)
        cls.mockDb.milestones.delete_one = Mock(wraps=cls.mockDb.milestones.delete_one)
        cls.mockDb.milestones.update_many = Mock(
            wraps=cls.mockDb.milestones.update_many
        )
        cls.mockDb.tasks.update_many = Mock(wraps=cls.mockDb.milestones.update_many)

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.milestones.delete_many({})

        opts = {
            "return_value": True,
            "side_effect": True,
        }
        self.mockDb.milestones.insert_one.reset_mock(**opts)
        self.mockDb.milestones.find_one_and_update.reset_mock(**opts)
        self.mockDb.milestones.find_one.reset_mock(**opts)
        self.mockDb.milestones.delete_one.reset_mock(**opts)
        self.mockDb.milestones.update_many.reset_mock(**opts)
        self.mockDb.tasks.update_many.reset_mock(**opts)

    def testCreateMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestoneResponse = self.createMilestone(
            user, project["id"], **self.testMilestone
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_200_OK)

        milestone = milestoneResponse.json()

        self.assertEqual(milestone["projectId"], project["id"])
        self.assertEqual(milestone["name"], self.testMilestone["name"])
        self.assertEqual(milestone["description"], self.testMilestone["description"])
        self.assertEqual(milestone["dueDate"], self.testMilestone["dueDate"])

        for v in milestone.values():
            self.assertIsNotNone(v)

    def testCreateMilestoneProjectNotFound(self):
        user = self.createUser("test")

        milestoneResponse = self.createMilestone(
            user, str(ObjectId()), **self.testMilestone
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateMilestoneUserNoAccess(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test").json()

        otherUser = self.createUser("other")

        milestoneResponse = self.createMilestone(
            otherUser, project["id"], **self.testMilestone
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testCreateMilestoneFailure(self):
        user = self.createUser("test")

        project = self.createProject(user, "test", "test").json()

        self.mockDb.milestones.insert_one.return_value.acknowledged = False

        milestoneResponse = self.createMilestone(
            user, project["id"], **self.testMilestone
        )

        self.assertEqual(
            milestoneResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testGetMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        createMilestoneResponse = self.createMilestone(
            user, project["id"], **self.testMilestone
        )

        self.assertEqual(createMilestoneResponse.status_code, status.HTTP_200_OK)

        milestoneResponse = self.client.get(
            f"/milestones/{createMilestoneResponse.json()['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_200_OK)

        milestone = milestoneResponse.json()

        self.assertEqual(milestone["projectId"], project["id"])
        self.assertEqual(milestone["name"], self.testMilestone["name"])
        self.assertEqual(milestone["description"], self.testMilestone["description"])
        self.assertEqual(milestone["dueDate"], self.testMilestone["dueDate"])

        for v in milestone.values():
            self.assertIsNotNone(v)

    def testGetMilestoneMilestoneNotFound(self):
        user = self.createUser("test")

        milestoneResponse = self.client.get(
            f"/milestones/{str(ObjectId())}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testGetMilestoneUserNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        otherUser = self.createUser("other")

        createMilestoneResponse = self.createMilestone(
            user, project["id"], **self.testMilestone
        )

        milestoneResponse = self.client.get(
            f"/milestones/{createMilestoneResponse.json()['id']}",
            headers=self.userToHeader(otherUser),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        milestoneName = "test2"
        milestoneDescription = "test2"
        milestoneDueDate = "2001-10-02T00:00:00"
        milestoneStatus = "In Progress"

        updateMilestoneResponse = self.client.patch(
            f"/milestones/{milestone['id']}",
            json={
                "name": milestoneName,
                "description": milestoneDescription,
                "dueDate": milestoneDueDate,
                "status": milestoneStatus,
            },
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateMilestoneResponse.status_code, status.HTTP_200_OK)

        milestone = updateMilestoneResponse.json()

        self.assertEqual(milestone["projectId"], project["id"])
        self.assertEqual(milestone["name"], milestoneName)
        self.assertEqual(milestone["description"], milestoneDescription)
        self.assertEqual(milestone["dueDate"], milestoneDueDate)
        self.assertEqual(milestone["status"], milestoneStatus)

        for v in milestone.values():
            self.assertIsNotNone(v)

    def testUpdateMilestoneNotFound(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        self.mockDb.milestones.find_one.return_value = None

        updateMilestoneResponse = self.client.patch(
            f"/milestones/{milestone['id']}",
            json={},
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateMilestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testUpdateMilestoneFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        self.mockDb.milestones.find_one_and_update.return_value = None

        updateMilestoneResponse = self.client.patch(
            f"/milestones/{milestone['id']}",
            json={},
            headers=self.userToHeader(user),
        )

        self.assertEqual(
            updateMilestoneResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testUpdateMilestoneMilestoneForbidden(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        otherUser = self.createUser("other")

        updateMilestoneResponse = self.client.patch(
            f"/milestones/{milestone['id']}",
            json={},
            headers=self.userToHeader(otherUser),
        )

        self.assertEqual(updateMilestoneResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testDeleteMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            "test",
            "test",
            "2001-10-01T00:00:00",
            {
                "name": "qatest",
                "description": "qatest",
                "dueDate": "2022-01-01T00:00:00",
            },
        ).json()

        milestone2 = self.createMilestone(
            user,
            project["id"],
            **self.testMilestone,
            args={
                "dependentMilestones": [milestone["id"]],
                "dependentTasks": [task["id"]],
            },
        ).json()

        deleteMilestoneResponse = self.client.delete(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(deleteMilestoneResponse.status_code, status.HTTP_200_OK)

        milestoneResponse = self.client.get(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(milestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

        milestone2Response = self.client.get(
            f"/milestones/{milestone2['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(milestone2Response.status_code, status.HTTP_200_OK)

        self.assertEqual(milestone2Response.json()["dependentMilestones"], [])

    def testDeleteMilestoneNotFound(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        self.mockDb.milestones.find_one.return_value = None

        deleteMilestoneResponse = self.client.delete(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(deleteMilestoneResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testDeleteMilestoneNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        otherUser = self.createUser("other")

        deleteMilestoneResponse = self.client.delete(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(otherUser),
        )

        self.assertEqual(deleteMilestoneResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testDeleteMilestoneFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        self.mockDb.milestones.delete_one.return_value.deleted_count = 0

        deleteMilestoneResponse = self.client.delete(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(
            deleteMilestoneResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteMilestoneUpdateMilstonesFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        self.mockDb.milestones.update_many.return_value.acknowledged = False

        deleteMilestoneResponse = self.client.delete(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(
            deleteMilestoneResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteMilestoneUpdateTasksFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], **self.testMilestone
        ).json()

        self.mockDb.tasks.update_many.return_value.acknowledged = False

        deleteMilestoneResponse = self.client.delete(
            f"/milestones/{milestone['id']}",
            headers=self.userToHeader(user),
        )

        self.assertEqual(
            deleteMilestoneResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

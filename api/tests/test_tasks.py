from unittest.mock import Mock

from bson import ObjectId
from fastapi import status

from api.tests.util import TestBase


class TestTasks(TestBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.testTask = {
            "name": "test",
            "description": "test",
            "dueDate": "2022-01-01T00:00:00",
            "qaTask": {
                "name": "qatest",
                "description": "qatest",
                "dueDate": "2022-01-01T00:00:00",
            },
        }

        cls.mockDb.tasks.insert_one = Mock(wraps=cls.mockDb.tasks.insert_one)
        cls.mockDb.tasks.find_one_and_update = Mock(
            wraps=cls.mockDb.tasks.find_one_and_update
        )
        cls.mockDb.tasks.delete_one = Mock(wraps=cls.mockDb.tasks.delete_one)
        cls.mockDb.milestones.update_many = Mock(
            wraps=cls.mockDb.milestones.update_many
        )
        cls.mockDb.tasks.update_many = Mock(wraps=cls.mockDb.tasks.update_many)

    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.milestones.delete_many({})
        self.mockDb.tasks.delete_many({})

        opts = {
            "return_value": True,
            "side_effect": True,
        }
        self.mockDb.tasks.insert_one.reset_mock(**opts)
        self.mockDb.tasks.find_one_and_update.reset_mock(**opts)
        self.mockDb.tasks.delete_one.reset_mock(**opts)
        self.mockDb.milestones.update_many.reset_mock(**opts)
        self.mockDb.tasks.update_many.reset_mock(**opts)

    def testCreateTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        taskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(taskResponse.status_code, 200)

        task = taskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], self.testTask["name"])
        self.assertEqual(task["description"], self.testTask["description"])
        self.assertEqual(task["dueDate"], self.testTask["dueDate"])
        self.assertEqual(task["qaTask"]["name"], self.testTask["qaTask"]["name"])
        self.assertEqual(
            task["qaTask"]["description"], self.testTask["qaTask"]["description"]
        )
        self.assertEqual(task["qaTask"]["dueDate"], self.testTask["qaTask"]["dueDate"])

        for v in task.values():
            self.assertIsNotNone(v)

    def testCreateTaskProjectNotFound(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        taskResponse = self.createTask(
            user,
            str(ObjectId()),
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(taskResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateTaskMilestoneNotFound(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        taskResponse = self.createTask(
            user,
            project["id"],
            str(ObjectId()),
            **self.testTask,
        )

        self.assertEqual(taskResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testCreateTaskMismatchProjectMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        project2 = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        taskResponse = self.createTask(
            user,
            project2["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(taskResponse.status_code, status.HTTP_400_BAD_REQUEST)

    def testCreateTaskNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()
        user2 = self.createUser("test2")

        taskResponse = self.createTask(
            user2,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(taskResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testCreateTaskFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        self.mockDb.tasks.insert_one.return_value.acknowledged = False

        taskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(
            taskResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testGetTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        createTaskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(createTaskResponse.status_code, status.HTTP_200_OK)

        task = createTaskResponse.json()

        getTaskResponse = self.client.get(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(getTaskResponse.status_code, status.HTTP_200_OK)

        task = getTaskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], self.testTask["name"])
        self.assertEqual(task["description"], self.testTask["description"])
        self.assertEqual(task["dueDate"], self.testTask["dueDate"])
        self.assertEqual(task["qaTask"]["name"], self.testTask["qaTask"]["name"])
        self.assertEqual(
            task["qaTask"]["description"], self.testTask["qaTask"]["description"]
        )
        self.assertEqual(task["qaTask"]["dueDate"], self.testTask["qaTask"]["dueDate"])

        for v in task.values():
            self.assertIsNotNone(v)

    def testGetTaskNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        createTaskResponse = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        user2 = self.createUser("test2")

        getTaskResponse = self.client.get(
            f"/tasks/{createTaskResponse.json()['id']}",
            headers=self.userToHeader(user2),
        )

        self.assertEqual(getTaskResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(task.status_code, status.HTTP_200_OK)

        task = task.json()

        updateTask = {
            "name": "updated",
            "description": "updated",
            "dueDate": "2022-01-01T00:00:00",
            "priority": "High",
            "qaTask": {
                "name": "updated",
                "description": "updated",
                "dueDate": "2022-01-01T00:00:00",
                "status": "In Progress",
            },
        }

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json=updateTask,
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, status.HTTP_200_OK)

        task = updateTaskResponse.json()

        self.assertEqual(task["projectId"], project["id"])
        self.assertEqual(task["milestoneId"], milestone["id"])
        self.assertEqual(task["name"], updateTask["name"])
        self.assertEqual(task["description"], updateTask["description"])
        self.assertEqual(task["dueDate"], updateTask["dueDate"])
        self.assertEqual(task["priority"], updateTask["priority"])
        self.assertEqual(task["qaTask"]["name"], updateTask["qaTask"]["name"])
        self.assertEqual(
            task["qaTask"]["description"], updateTask["qaTask"]["description"]
        )
        self.assertEqual(task["qaTask"]["dueDate"], updateTask["qaTask"]["dueDate"])
        self.assertEqual(task["qaTask"]["status"], updateTask["qaTask"]["status"])

        for v in task.values():
            self.assertIsNotNone(v)

    def testUpdateTaskProjectAndMilestone(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        self.assertEqual(task.status_code, status.HTTP_200_OK)

        task = task.json()

        newProject = self.createProject(user, "test", "test").json()
        newMilestone = self.createMilestone(
            user, newProject["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        updateTask = {
            "projectId": newProject["id"],
            "milestoneId": newMilestone["id"],
        }

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json=updateTask,
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, status.HTTP_200_OK)

        task = updateTaskResponse.json()

        self.assertEqual(task["projectId"], newProject["id"])
        self.assertEqual(task["milestoneId"], newMilestone["id"])

    def testUpdateTaskProjectNotFound(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        updateTask = {
            "projectId": str(ObjectId()),
        }

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json=updateTask,
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testUpdateTaskMilestoneNotFound(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        updateTask = {
            "milestoneId": str(ObjectId()),
        }

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json=updateTask,
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testUpdateTaskNotFound(self):
        user = self.createUser("test")

        updateTaskResponse = self.client.patch(
            f"/tasks/{str(ObjectId())}",
            json={},
            headers=self.userToHeader(user),
        )

        self.assertEqual(updateTaskResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testUpdateTaskNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        user2 = self.createUser("test2")

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json={},
            headers=self.userToHeader(user2),
        )

        self.assertEqual(updateTaskResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testUpdateTaskFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        self.mockDb.tasks.find_one_and_update.return_value = None

        updateTaskResponse = self.client.patch(
            f"/tasks/{task['id']}",
            json={},
            headers=self.userToHeader(user),
        )

        self.assertEqual(
            updateTaskResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteTask(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )
        task2 = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
            args={"dependentTasks": [task.json()["id"]]},
        )
        self.assertEqual(task.status_code, status.HTTP_200_OK)
        self.assertEqual(task2.status_code, status.HTTP_200_OK)

        task = task.json()
        task2 = task2.json()

        deleteTaskResponse = self.client.delete(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )
        self.assertEqual(deleteTaskResponse.status_code, status.HTTP_200_OK)

        getTaskResponse = self.client.get(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )
        self.assertEqual(getTaskResponse.status_code, status.HTTP_404_NOT_FOUND)

        getTaskResponse = self.client.get(
            f"/tasks/{task2['id']}", headers=self.userToHeader(user)
        )
        self.assertEqual(getTaskResponse.status_code, status.HTTP_200_OK)

        task2 = getTaskResponse.json()
        self.assertEqual(task2["dependentTasks"], [])

    def testDeleteTaskNotFound(self):
        user = self.createUser("test")

        deleteTaskResponse = self.client.delete(
            f"/tasks/{str(ObjectId())}", headers=self.userToHeader(user)
        )
        self.assertEqual(deleteTaskResponse.status_code, status.HTTP_404_NOT_FOUND)

    def testDeleteTaskNoAccess(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()
        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        user2 = self.createUser("test2")

        deleteTaskResponse = self.client.delete(
            f"/tasks/{task['id']}", headers=self.userToHeader(user2)
        )

        self.assertEqual(deleteTaskResponse.status_code, status.HTTP_403_FORBIDDEN)

    def testDeleteTaskFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()
        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        self.mockDb.tasks.delete_one.return_value.deleted_count = 0

        deleteTaskResponse = self.client.delete(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteTaskResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteTasksUpdateMilestoneFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        self.mockDb.milestones.update_many.return_value.acknowledged = False

        deleteTaskResponse = self.client.delete(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteTaskResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    def testDeleteTasksUpdateTaskFailure(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()
        milestone = self.createMilestone(
            user, project["id"], "test", "test", "2022-01-01T00:00:00"
        ).json()

        task = self.createTask(
            user,
            project["id"],
            milestone["id"],
            **self.testTask,
        )

        task = task.json()

        self.mockDb.tasks.update_many.return_value.acknowledged = False

        deleteTaskResponse = self.client.delete(
            f"/tasks/{task['id']}", headers=self.userToHeader(user)
        )

        self.assertEqual(
            deleteTaskResponse.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR
        )

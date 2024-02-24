from fastapi import status

from api.tests.util import TestBase


class TestSprints(TestBase):
    def tearDown(self) -> None:
        self.mockDb.users.delete_many({})
        self.mockDb.projects.delete_many({})
        self.mockDb.sprints.delete_many({})

    def createSprint(
        self,
        user,
        projectId,
        name,
        description,
        startDate,
        endDate,
    ):
        return self.client.post(
            f"/sprints/",
            headers=self.userToHeader(user),
            json={
                "name": name,
                "projectId": projectId,
                "description": description,
                "startDate": startDate,
                "endDate": endDate,
            },
        )

    def testCreateSprint(self):
        user = self.createUser("test")
        project = self.createProject(user, "test", "test").json()

        sprintName = "test"
        sprintDescription = "test"
        sprintStartDate = "2001-10-01T00:00:00"
        sprintEndDate = "2001-11-01T00:00:00"

        sprintResponse = self.createSprint(
            user,
            project["id"],
            sprintName,
            sprintDescription,
            sprintStartDate,
            sprintEndDate,
        )

        self.assertEqual(sprintResponse.status_code, status.HTTP_200_OK)

        sprint = sprintResponse.json()

        self.assertEqual(sprint["projectId"], project["id"])
        self.assertEqual(sprint["name"], sprintName)
        self.assertEqual(sprint["description"], sprintDescription)
        self.assertEqual(sprint["startDate"], sprintStartDate)
        self.assertEqual(sprint["endDate"], sprintEndDate)

        for v in sprint.values():
            self.assertIsNotNone(v)

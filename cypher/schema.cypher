CREATE CONSTRAINT ON (platform:Platform) ASSERT platform.name IS UNIQUE;
CREATE CONSTRAINT ON (project:Project) ASSERT project.name IS UNIQUE;
CREATE CONSTRAINT ON (project:Project) ASSERT project.ID IS UNIQUE;
CREATE CONSTRAINT ON (version:Version) ASSERT version.number IS UNIQUE;
CREATE CONSTRAINT ON (language:Language) ASSERT language.name IS UNIQUE;
CREATE CONSTRAINT ON (c:Contributor) ASSERT c.uuid IS UNIQUE;

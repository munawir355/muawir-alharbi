-- Drop the database 'COMP2001'
-- Connect to the 'master' database to run this snippet
USE master
GO
-- Uncomment the ALTER DATABASE statement below to set the database to SINGLE_USER mode if the drop database command fails because the database is in use.
ALTER DATABASE COMP2001 SET SINGLE_USER WITH ROLLBACK IMMEDIATE;
-- Drop the database if it exists
IF EXISTS (
    SELECT [name]
        FROM sys.databases
        WHERE [name] = N'COMP2001'
)
DROP DATABASE COMP2001
GO

-- Create the new database if it does not exist already
IF NOT EXISTS (
    SELECT [name]
        FROM sys.databases
        WHERE [name] = N'COMP2001'
)
CREATE DATABASE COMP2001
GO


USE COMP2001;
GO

-- Create User Table under CW1 schema
CREATE SCHEMA CW1;
GO

CREATE TABLE CW1.[User] (
    UserID INT PRIMARY KEY,
    Name VARCHAR(100) NOT NULL,
    Email VARCHAR(150) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL
);

-- Create Trail Table under CW1 schema
CREATE TABLE CW1.Trail (
    TrailID INT PRIMARY KEY,
    TrailName VARCHAR(150) NOT NULL,
    Description TEXT,
    DateCreated DATE NOT NULL,
    CreatedBy INT NOT NULL,
    FOREIGN KEY (CreatedBy) REFERENCES CW1.[User](UserID)
);

-- Create UserTrail Table (Link Entity) under CW1 schema
CREATE TABLE CW1.UserTrail (
    UserTrailID INT PRIMARY KEY,
    UserID INT NOT NULL,
    TrailID INT NOT NULL,
    FOREIGN KEY (UserID) REFERENCES CW1.[User](UserID),
    FOREIGN KEY (TrailID) REFERENCES CW1.Trail(TrailID)
);


-- Insert data into User table
INSERT INTO CW1.[User] (UserID, Name, Email, Password) VALUES
(1, 'John Doe', 'john@example.com', 'password123'),
(2, 'Jane Smith', 'jane@example.com', 'securepass'),
(3, 'Grace Hopper', 'grace@plymouth.ac.uk', 'ISAD123!'),
(4, 'Tim Berners-Lee', 'tim@plymouth.ac.uk', 'COMP2001!'),
(5, 'Ada Lovelace', 'ada@plymouth.ac.uk', 'insecurePassword');

-- Insert data into Trail table
INSERT INTO CW1.Trail (TrailID, TrailName, Description, DateCreated, CreatedBy) VALUES
(1, 'Plymbridge Trail', 'A scenic trail through Plymbridge woods.', '2024-01-15', 1),
(2, 'Waterfront Trail', 'Trail along the waterfront area.', '2024-02-10', 2);

-- Insert data into UserTrail table
INSERT INTO CW1.UserTrail (UserTrailID, UserID, TrailID) VALUES
(1, 1, 1),  -- John Doe follows Plymbridge Trail
(2, 2, 2);  -- Jane Smith follows Waterfront Trail


-- Verify data in User table
SELECT * FROM CW1.[User];

-- Verify data in Trail table
SELECT * FROM CW1.Trail;

-- Verify data in UserTrail table
SELECT * FROM CW1.UserTrail;
GO


-- Create a view to combine Trail and User data
CREATE VIEW CW1.TrailDetails AS
SELECT
    t.TrailID,
    t.TrailName,
    t.Description,
    t.DateCreated,
    u.Name AS CreatedBy
FROM
    CW1.Trail t
JOIN
    CW1.[User] u ON t.CreatedBy = u.UserID;

GO

-- Verify the view returns data
SELECT * FROM CW1.TrailDetails;
GO


-- SQL Scripts for Stored Procedures

-- Insert Procedure:

IF EXISTS (
SELECT *
    FROM INFORMATION_SCHEMA.ROUTINES
WHERE SPECIFIC_SCHEMA = N'CW1'
    AND SPECIFIC_NAME = N'AddNewTrail'
)
DROP PROCEDURE  CW1.AddNewTrail
GO


CREATE PROCEDURE CW1.AddNewTrail(
    @TrailID INT,
    @TrailName VARCHAR(150),
    @Description TEXT,
    @DateCreated DATE,
    @CreatedBy INT
)
AS
BEGIN
    INSERT INTO CW1.Trail (TrailID, TrailName, Description, DateCreated, CreatedBy)
    VALUES (@TrailID, @TrailName, @Description, @DateCreated, @CreatedBy);
END;

GO
-- Read Procedure:


CREATE PROCEDURE CW1.GetTrails
AS
BEGIN
    SELECT * FROM CW1.Trail;
END;

GO
-- Update Procedure:


CREATE PROCEDURE CW1.UpdateTrail(
    @TrailID INT,
    @TrailName VARCHAR(150),
    @Description TEXT
)
AS
BEGIN
    UPDATE CW1.Trail
    SET TrailName = @TrailName, Description = @Description
    WHERE TrailID = @TrailID;
END;

GO
-- Delete Procedure:


CREATE PROCEDURE CW1.DeleteTrail(@TrailID INT)
AS
BEGIN
    DELETE FROM CW1.Trail WHERE TrailID = @TrailID;
END;

GO

-- Check existing trails in CW1.Trail table
SELECT * FROM CW1.Trail;

GO

-- Add a new trail using the AddNewTrail procedure
EXEC CW1.AddNewTrail
    @TrailID = 3,
    @TrailName = 'Mountain View Trail',
    @Description = 'A challenging trail with beautiful mountain views.',
    @DateCreated = '2024-04-01',
    @CreatedBy = 1;

GO

-- Verify the new trail was added
SELECT * FROM CW1.Trail;

GO

-- Retrieve all trails using GetTrails procedure
EXEC CW1.GetTrails;

GO

-- Check existing trail details
SELECT * FROM CW1.Trail WHERE TrailID = 1;
GO

-- Update trail name and description using the UpdateTrail procedure
EXEC CW1.UpdateTrail
    @TrailID = 1,
    @TrailName = 'Updated Plymbridge Trail',
    @Description = 'An updated scenic trail through Plymbridge woods.';

GO

-- Verify the trail details were updated
SELECT * FROM CW1.Trail WHERE TrailID = 1;

GO

-- Check existing trails
SELECT * FROM CW1.Trail;
GO

-- Delete a trail using the DeleteTrail procedure
EXEC CW1.DeleteTrail @TrailID = 3;
GO

-- Verify the trail was deleted
SELECT * FROM CW1.Trail;
GO

-- Create log table
CREATE TABLE CW1.TrailLog (
    LogID INT PRIMARY KEY IDENTITY(1,1),
    TrailID INT,
    Action VARCHAR(50),
    ActionTime DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (TrailID) REFERENCES CW1.Trail(TrailID)
);
GO

-- Create trigger
CREATE TRIGGER CW1.trgAfterInsertTrail
ON CW1.Trail
AFTER INSERT
AS
BEGIN
    INSERT INTO CW1.TrailLog (TrailID, Action)
    SELECT TrailID, 'INSERT'
    FROM inserted;
END;
GO

-- Insert a new trail to test the trigger
INSERT INTO CW1.Trail (TrailID, TrailName, Description, DateCreated, CreatedBy)
VALUES (3, 'Forest Trail', 'A trail through the forest.', '2024-03-01', 1);
GO

-- Verify the log
SELECT * FROM CW1.TrailLog;
GO

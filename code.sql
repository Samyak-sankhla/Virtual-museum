-- =========================================================
-- Virtual Museum - FINAL combined schema + complex queries + procedures/functions
-- =========================================================

DROP DATABASE IF EXISTS virtual_museum;
CREATE DATABASE virtual_museum;
USE virtual_museum;

-- =========================================================
-- USERS
-- =========================================================
CREATE TABLE User (
    User_ID INT AUTO_INCREMENT PRIMARY KEY,
    Fname VARCHAR(60) NOT NULL,
    Lname VARCHAR(60) NOT NULL,
    Email VARCHAR(150) UNIQUE NOT NULL,
    Password VARCHAR(255) NOT NULL,
    Role ENUM('Customer','Artist','Admin') DEFAULT 'Customer',
    Contact_No VARCHAR(20),
    Address TEXT,
    Bio TEXT,
    Profile_Pic BLOB,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (CHAR_LENGTH(Fname) > 0 AND CHAR_LENGTH(Lname) > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_user_role ON User(Role);

-- =========================================================
-- MUSEUMS
-- =========================================================
CREATE TABLE Museum (
    M_ID INT AUTO_INCREMENT PRIMARY KEY,
    Name VARCHAR(150) NOT NULL,
    Location VARCHAR(200),
    Capacity INT DEFAULT 100 CHECK (Capacity >= 0),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_museum_name (Name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- ARTIFACTS
-- =========================================================
CREATE TABLE Artifact (
    Artifact_ID INT AUTO_INCREMENT PRIMARY KEY,
    Artist_ID INT,
    M_ID INT,
    Title VARCHAR(150) NOT NULL,
    Description TEXT,
    Type ENUM('Painting','Sculpture','Digital','Photography','Other') DEFAULT 'Other',
    Quality VARCHAR(50),
    Owner VARCHAR(150),
    Price DECIMAL(12,2) NOT NULL DEFAULT 0.00 CHECK (Price >= 0),
    Quantity INT DEFAULT 0 CHECK (Quantity >= 0),
    Image VARCHAR(255),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (Artist_ID) REFERENCES User(User_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (M_ID)     REFERENCES Museum(M_ID) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_artifact_title  ON Artifact (Title);
CREATE INDEX idx_artifact_type   ON Artifact (Type);
CREATE INDEX idx_artifact_museum ON Artifact (M_ID);
CREATE INDEX idx_artifact_qty    ON Artifact (Quantity);

-- =========================================================
-- EXHIBITIONS
-- =========================================================
CREATE TABLE Exhibition (
    Exhibition_ID INT AUTO_INCREMENT PRIMARY KEY,
    Title VARCHAR(150) NOT NULL,
    Theme VARCHAR(150),
    Start_Date DATE,
    End_Date DATE,
    Description TEXT,
    M_ID INT,
    Capacity INT DEFAULT 200,
    Artist_ID INT,
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_exhibition_dates CHECK (End_Date IS NULL OR End_Date >= Start_Date),
    FOREIGN KEY (M_ID)     REFERENCES Museum(M_ID) ON DELETE SET NULL ON UPDATE CASCADE,
    FOREIGN KEY (Artist_ID) REFERENCES User(User_ID) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_ex_start ON Exhibition (Start_Date);
CREATE INDEX idx_ex_m     ON Exhibition (M_ID);

-- =========================================================
-- VIRTUAL RECORDS
-- =========================================================
CREATE TABLE Virtual_Record (
    VR_ID INT AUTO_INCREMENT PRIMARY KEY,
    A_ID INT UNIQUE,
    Service VARCHAR(150),
    VR_Link VARCHAR(255),
    Created_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (A_ID) REFERENCES Artifact(Artifact_ID) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- EXHIBITION_ARTIFACT
-- =========================================================
CREATE TABLE Exhibition_Artifact (
    Exhibition_ID INT,
    Artifact_ID INT,
    Display_Order INT DEFAULT 1 CHECK (Display_Order > 0),
    PRIMARY KEY (Exhibition_ID, Artifact_ID),
    FOREIGN KEY (Exhibition_ID) REFERENCES Exhibition(Exhibition_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Artifact_ID)   REFERENCES Artifact(Artifact_ID)     ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- ATTENDS
-- =========================================================
CREATE TABLE Attends (
    C_ID INT,
    E_ID INT,
    Attended_At TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (C_ID, E_ID),
    FOREIGN KEY (C_ID) REFERENCES User(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (E_ID) REFERENCES Exhibition(Exhibition_ID) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- VISITS
-- =========================================================
CREATE TABLE Visits (
    C_ID INT,
    M_ID INT,
    Visit_Date DATE DEFAULT (CURRENT_DATE),
    Purpose VARCHAR(150),
    PRIMARY KEY (C_ID, M_ID),
    FOREIGN KEY (C_ID) REFERENCES User(User_ID) ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (M_ID) REFERENCES Museum(M_ID) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =========================================================
-- PURCHASES
-- =========================================================
CREATE TABLE Purchase (
    Purchase_ID INT AUTO_INCREMENT PRIMARY KEY,
    Customer_ID INT NOT NULL,
    Artifact_ID INT NOT NULL,
    Purchase_Date DATETIME DEFAULT CURRENT_TIMESTAMP,
    Quantity INT DEFAULT 1 CHECK (Quantity > 0),
    Total_Amount DECIMAL(12,2),
    Payment_Method ENUM('Card','UPI','Cash','NetBanking') DEFAULT 'Card',
    FOREIGN KEY (Customer_ID) REFERENCES User(User_ID)     ON DELETE CASCADE ON UPDATE CASCADE,
    FOREIGN KEY (Artifact_ID) REFERENCES Artifact(Artifact_ID) ON DELETE RESTRICT ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_purchase_date     ON Purchase (Purchase_Date);
CREATE INDEX idx_purchase_customer ON Purchase (Customer_ID);
CREATE INDEX idx_purchase_artifact ON Purchase (Artifact_ID);

-- =========================================================
-- TRIGGERS
-- =========================================================
DELIMITER //

DROP TRIGGER IF EXISTS trg_before_purchase;
CREATE TRIGGER trg_before_purchase
BEFORE INSERT ON Purchase
FOR EACH ROW
BEGIN
    DECLARE stock INT;
    SELECT Quantity INTO stock
    FROM Artifact
    WHERE Artifact_ID = NEW.Artifact_ID
    FOR UPDATE;
    IF stock IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artifact not found';
    ELSEIF NEW.Quantity > stock THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock';
    ELSE
        UPDATE Artifact
        SET Quantity = Quantity - NEW.Quantity
        WHERE Artifact_ID = NEW.Artifact_ID;
    END IF;
END;//

DROP TRIGGER IF EXISTS trg_before_attend;
CREATE TRIGGER trg_before_attend
BEFORE INSERT ON Attends
FOR EACH ROW
BEGIN
    DECLARE attendees INT;
    DECLARE cap INT;
    SELECT COUNT(*) INTO attendees FROM Attends WHERE E_ID = NEW.E_ID;
    SELECT Capacity INTO cap FROM Exhibition WHERE Exhibition_ID = NEW.E_ID;
    IF cap IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Exhibition not found';
    ELSEIF attendees >= cap THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Exhibition capacity full';
    END IF;
END;//

DROP TRIGGER IF EXISTS trg_validate_exhibition_artist;
CREATE TRIGGER trg_validate_exhibition_artist
BEFORE INSERT ON Exhibition
FOR EACH ROW
BEGIN
    DECLARE r ENUM('Customer','Artist','Admin');
    SELECT Role INTO r FROM User WHERE User_ID = NEW.Artist_ID;
    IF r IS NULL THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Artist_ID not found';
    ELSEIF r <> 'Artist' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Only artists can organize exhibitions';
    END IF;
END;//

DELIMITER ;

-- =========================================================
-- VIEWS
-- =========================================================
CREATE OR REPLACE VIEW AdminTransactionRecords AS
SELECT 
    p.Purchase_ID  AS Transaction_ID,
    p.Purchase_Date,
    CONCAT(c.Fname,' ',c.Lname) AS Customer_Name,
    a.Title         AS Artifact_Title,
    p.Quantity,
    p.Total_Amount,
    CONCAT(ar.Fname,' ',ar.Lname) AS Artist_Name,
    m.Name          AS Museum_Name
FROM Purchase p
JOIN User     c  ON p.Customer_ID   = c.User_ID
JOIN Artifact a  ON p.Artifact_ID   = a.Artifact_ID
LEFT JOIN User   ar ON a.Artist_ID  = ar.User_ID
LEFT JOIN Museum m  ON a.M_ID       = m.M_ID
ORDER BY p.Purchase_Date DESC, p.Purchase_ID DESC;

CREATE OR REPLACE VIEW v_customers_above_avg_spend AS
SELECT CONCAT(u.Fname,' ',u.Lname) AS CustomerName
FROM User u
WHERE u.User_ID IN (
    SELECT p.Customer_ID
    FROM Purchase p
    GROUP BY p.Customer_ID
    HAVING SUM(p.Total_Amount) > (
        SELECT AVG(ps.TotalAll)
        FROM (
            SELECT SUM(p2.Total_Amount) AS TotalAll
            FROM Purchase p2
            GROUP BY p2.Customer_ID
        ) AS ps
    )
);

CREATE OR REPLACE VIEW v_artifacts_above_artist_avg_price AS
SELECT a1.Artifact_ID, a1.Title, a1.Price, a1.Artist_ID
FROM Artifact a1
WHERE a1.Price > (
    SELECT AVG(a2.Price)
    FROM Artifact a2
    WHERE a2.Artist_ID = a1.Artist_ID
);

CREATE OR REPLACE VIEW v_artists_with_multiple_artifacts_sold AS
SELECT a.Artist_ID,
       CONCAT(u.Fname,' ',u.Lname) AS ArtistName,
       COUNT(DISTINCT p.Artifact_ID) AS Artifacts_Sold
FROM Artifact a
JOIN Purchase p ON a.Artifact_ID = p.Artifact_ID
JOIN User u     ON a.Artist_ID   = u.User_ID
GROUP BY a.Artist_ID, ArtistName
HAVING Artifacts_Sold > 1;

CREATE OR REPLACE VIEW v_museum_sales_ranked AS
WITH MuseumSales AS (
    SELECT m.M_ID, m.Name, IFNULL(SUM(p.Total_Amount),0) AS Total_Sales
    FROM Museum m
    LEFT JOIN Artifact a ON a.M_ID = m.M_ID
    LEFT JOIN Purchase p ON p.Artifact_ID = a.Artifact_ID
    GROUP BY m.M_ID, m.Name
)
SELECT M_ID, Name, Total_Sales,
       RANK() OVER (ORDER BY Total_Sales DESC) AS Sales_Rank
FROM MuseumSales;

CREATE OR REPLACE VIEW v_typewise_most_expensive_artifact AS
SELECT a.Type AS Artifact_Type,
       a.Artifact_ID,
       a.Title  AS Artifact_Title,
       CONCAT(u.Fname, ' ', u.Lname) AS Artist_Name,
       a.Price
FROM Artifact a
JOIN User u ON a.Artist_ID = u.User_ID
WHERE a.Price = (
    SELECT MAX(a2.Price) FROM Artifact a2 WHERE a2.Type = a.Type
);

-- =========================================================
-- SAMPLE DATA
-- =========================================================
INSERT INTO User (Fname, Lname, Email, Password, Role, Contact_No, Address, Bio) VALUES
('Alice','Painter','alice@vm.com','alice123','Artist','+911234567890','Mumbai, India','Contemporary artist'),
('Bob','Sculptor','bob@vm.com','bob123','Artist','+911234567891','Delhi, India','Bronze sculptor'),
('Charlie','Viewer','charlie@vm.com','charlie123','Customer','+911234567892','Kolkata, India','Likes digital art'),
('Diana','Collector','diana@vm.com','diana123','Customer','+911234567893','Chennai, India','Collector'),
('Admin','One','admin@vm.com','admin123','Admin','+919999999999','Hyderabad, India','Sys admin');

INSERT INTO Museum (Name, Location, Capacity) VALUES
('National Art House','Mumbai, India',500),
('Digital Gallery','Bengaluru, India',300);

INSERT INTO Artifact (Artist_ID, M_ID, Title, Description, Type, Quality, Owner, Price, Quantity, Image) VALUES
(1,1,'Sunset Bliss','An oil painting of a sunset.','Painting','Excellent','Alice Painter',2500.00,10,'uploads/sunset_bliss.jpeg'),
(1,1,'Night Glow','Acrylic painting under UV light.','Painting','Good','Alice Painter',1800.00,5,'uploads/night_glow.jpg'),
(2,1,'Bronze Warrior','Detailed sculpture of a warrior.','Sculpture','Very Good','Bob Sculptor',5000.00,2,'uploads/bronze_warrior.jpg'),
(2,2,'Marble Angel','Elegant marble statue.','Sculpture','Excellent','Bob Sculptor',8000.00,1,'uploads/marble_angel.jpg'),
(1,2,'Digital Dream','3D generated surreal art.','Digital','Good','Alice Painter',1200.00,8,'uploads/digital_dream.jpg');

INSERT INTO Exhibition (Title, Theme, Start_Date, End_Date, Description, M_ID, Artist_ID, Capacity) VALUES
('Modern Wonders','Modern Art','2025-11-01','2025-12-15','Showcasing modern creations.',1,1,200),
('SculptFest','Sculpture','2025-12-20','2026-01-30','Dedicated to sculptures.',1,2,150),
('Virtual Visions','Digital Art','2026-02-01','2026-03-15','Futuristic digital art show.',2,1,120);

INSERT INTO Exhibition_Artifact VALUES (1,1,1),(1,2,2),(2,3,1),(3,5,1);

INSERT INTO Attends VALUES (3,1,DEFAULT),(4,1,DEFAULT),(3,3,DEFAULT);

INSERT INTO Visits  VALUES (3,1,'2025-10-20','Tour'),(4,1,'2025-10-22','Purchase'),(3,2,'2025-10-25','Virtual Tour');

INSERT INTO Purchase (Customer_ID, Artifact_ID, Quantity, Total_Amount, Payment_Method)
VALUES
(3,1,1,2500.00,'UPI'),
(3,2,2,3600.00,'Card'),
(4,3,1,5000.00,'NetBanking');

-- =========================================================
-- DB USERS & PRIVILEGES
-- =========================================================
CREATE USER IF NOT EXISTS 'museum_user'@'localhost' IDENTIFIED BY 'user123';
CREATE USER IF NOT EXISTS 'museum_admin'@'localhost' IDENTIFIED BY 'admin123';
GRANT SELECT ON virtual_museum.* TO 'museum_user'@'localhost';
GRANT ALL PRIVILEGES ON virtual_museum.* TO 'museum_admin'@'localhost';
FLUSH PRIVILEGES;

-- =========================================================
-- STORED PROCEDURE & FUNCTION
-- =========================================================
DELIMITER //

-- Procedure: Get total purchases by customer
CREATE PROCEDURE sp_get_customer_total(IN cust_id INT, OUT total DECIMAL(12,2))
BEGIN
    SELECT IFNULL(SUM(Total_Amount),0) INTO total
    FROM Purchase
    WHERE Customer_ID = cust_id;
END //

-- Function: Get stock for an artifact
CREATE FUNCTION fn_get_artifact_stock(a_id INT)
RETURNS INT
DETERMINISTIC
BEGIN
    DECLARE qty INT;
    SELECT IFNULL(Quantity,0) INTO qty
    FROM Artifact
    WHERE Artifact_ID = a_id;
    RETURN qty;
END //

DELIMITER ;

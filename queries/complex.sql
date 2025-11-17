-- name: Customers above average total spend
SELECT CONCAT(u.Fname,' ',u.Lname) AS CustomerName
FROM User u
WHERE u.User_ID IN (
    SELECT p.Customer_ID FROM Purchase p GROUP BY p.Customer_ID
    HAVING SUM(p.Total_Amount) > (
        SELECT AVG(ps.TotalAll)
        FROM (SELECT SUM(p2.Total_Amount) AS TotalAll FROM Purchase p2 GROUP BY p2.Customer_ID) AS ps
    )
);

-- name: Artifacts priced above artist's average
SELECT a1.Title, a1.Price, a1.Artist_ID
FROM Artifact a1
WHERE a1.Price > (
    SELECT AVG(a2.Price)
    FROM Artifact a2
    WHERE a2.Artist_ID = a1.Artist_ID
);

-- name: Artists with >1 distinct artifact sold
SELECT a.Artist_ID, CONCAT(u.Fname,' ',u.Lname) AS ArtistName,
       COUNT(DISTINCT p.Artifact_ID) AS Artifacts_Sold
FROM Artifact a
JOIN Purchase p ON a.Artifact_ID = p.Artifact_ID
JOIN User u ON a.Artist_ID = u.User_ID
GROUP BY a.Artist_ID
HAVING Artifacts_Sold > 1;

-- name: Museum sales ranking
WITH MuseumSales AS (
    SELECT m.M_ID, m.Name, IFNULL(SUM(p.Total_Amount),0) AS Total_Sales
    FROM Museum m
    LEFT JOIN Artifact a ON a.M_ID = m.M_ID
    LEFT JOIN Purchase p ON p.Artifact_ID = a.Artifact_ID
    GROUP BY m.M_ID
)
SELECT M_ID, Name, Total_Sales,
       RANK() OVER (ORDER BY Total_Sales DESC) AS Sales_Rank
FROM MuseumSales;

-- name: Most expensive artifact per type
SELECT a.Type AS Artifact_Type,
       a.Title AS Artifact_Title,
       CONCAT(u.Fname, ' ', u.Lname) AS Artist_Name,
       a.Price
FROM Artifact a
JOIN User u ON a.Artist_ID = u.User_ID
WHERE a.Price = (
    SELECT MAX(a2.Price)
    FROM Artifact a2
    WHERE a2.Type = a.Type
);

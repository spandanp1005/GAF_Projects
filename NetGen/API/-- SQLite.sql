-- SQLite
CREATE TABLE Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            
INSERT INTO Users ( email, password) VALUES ("spatel@gmail.com", "spatel123")
INSERT INTO Users ( email, password) VALUES ("jsmith@gmail.com", "jsmith123")                
INSERT INTO Users ( email, password) VALUES ("jdoe@gmail.com", "jdoe123")
SELECT * FROM Users 
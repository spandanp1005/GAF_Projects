-- SQLite
CREATE TABLE Users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            
INSERT INTO Users ( email, password) VALUES ("spatel@gmail.com", "pwd")
                

-- login tables, run this after schema_full.sql
-- signup = name + username + password, login = username + password
-- no email or any verification, so one person can make as many accounts as they like

CREATE TABLE users (
    -- username is the PRIMARY KEY(UNIQUE) 
    username VARCHAR(20) PRIMARY KEY 
        CHECK (username NOT IN ('admin', 'administrator', 'root', 'support', 'system', 'flexi', 'flexiadmin')),
    
    name VARCHAR(100) NOT NULL CHECK (length(trim(name)) > 0),
    
    -- only the hash goes here (bcrypt or argon2). Enforce that it cannot be blank.
    password_hash TEXT NOT NULL CHECK (length(password_hash) > 0), 
    
    -- not asked at signup, the student picks it later in preferences
    hostel_id INTEGER REFERENCES messes(mess_id) ON DELETE SET NULL,
    
    role VARCHAR(10) NOT NULL DEFAULT 'student' CHECK (role IN ('student', 'admin')),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- for locking the account after too many wrong passwords
    failed_login_count INTEGER NOT NULL DEFAULT 0 CHECK (failed_login_count >= 0),
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_login_at TIMESTAMPTZ
);

CREATE TABLE sessions (
    session_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    -- Updated to reference username instead of user_id
    username VARCHAR(20) NOT NULL REFERENCES users(username) ON DELETE CASCADE ON UPDATE CASCADE,
    
    -- sha-256 of the token as 64 hex characters, the token itself is never saved
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at TIMESTAMPTZ NOT NULL,
    last_used_at TIMESTAMPTZ,
    CHECK (expires_at > created_at)
);

-- Updated indexes for username lookup performance
CREATE INDEX sessions_username_idx ON sessions (username);
CREATE INDEX sessions_expires_idx ON sessions (expires_at);

-- to clear out old sessions now and then:
-- DELETE FROM sessions WHERE expires_at < now();

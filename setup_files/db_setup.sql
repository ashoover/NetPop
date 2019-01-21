-- CREATE DATABASE netpop;

USE netpop;

-- Users Table Creation
CREATE TABLE users (
    uid INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, 
    firstname VARCHAR(30), 
    lastname VARCHAR(30), 
    username VARCHAR(20), 
    mobilenum VARCHAR(11),
    password VARCHAR(100), 
    email VARCHAR(50), 
    settings VARCHAR(3000), 
    rank INT(3), 
    lastlogin VARCHAR(20),
    last_invalid_login VARCHAR(20),
    reset_token VARCHAR(50)
)
ENGINE=MyISAM
DEFAULT CHARSET=utf8
COLLATE=utf8_general_ci;


-- Endpoints Table Creation
CREATE TABLE endpoints (
    uid INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY, 
    hostname VARCHAR(50),
    ip VARCHAR(15),
    zip INT(10),
    last_check VARCHAR(24),
    enabled BOOL,
    endabled_date VARCHAR(24),
    disabled_date VARCHAR(24),
    creation_date VARCHAR(24),
    endpoint_name VARCHAR(50);
)
ENGINE=MyISAM
DEFAULT CHARSET=utf8
COLLATE=utf8_general_ci;


-- Enpoint Logs Table Creation
CREATE TABLE endpoint_log (
	uid INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
	check_time varchar(24) NULL,
	response_time varchar(10) NULL,
	endpoint_alive BOOL NULL,
	notice_sent BOOL NULL,
	notice_time_sent varchar(24) NULL
)
ENGINE=MyISAM
DEFAULT CHARSET=utf8
COLLATE=utf8_general_ci;


-- Contact Logs Table Creation
CREATE TABLE cont_log (
	uid INT(11) NOT NULL AUTO_INCREMENT PRIMARY KEY,
	recipient varchar(100) NULL,
	date_sent varchar(100) NULL,
	message_type varchar(100) NULL,
	CONSTRAINT cont_log_pk PRIMARY KEY (uid)
)
ENGINE=MyISAM
DEFAULT CHARSET=utf8
COLLATE=utf8_general_ci;

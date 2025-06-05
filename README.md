# Crewly Backend

Shift scheduling application backend built with Flask and SQLAlchemy.

## Overview
This is the backend API component of the Crewly application, a shift scheduling assistant designed to help businesses transition from paper-based scheduling to digital solutions.

## Setup Instructions
1. Create and activate virtual environment: 
   
2. Install dependencies: Collecting Flask==3.1.0
  Using cached flask-3.1.0-py3-none-any.whl (102 kB)
Collecting Flask-SQLAlchemy==3.1.1
  Using cached flask_sqlalchemy-3.1.1-py3-none-any.whl (25 kB)
Collecting PyMySQL==1.1.1
  Using cached PyMySQL-1.1.1-py3-none-any.whl (44 kB)
Collecting SQLAlchemy==2.0.40
  Using cached sqlalchemy-2.0.40-cp311-cp311-manylinux_2_17_x86_64.manylinux2014_x86_64.whl (3.2 MB)
Collecting cryptography==36.0.2
  Using cached cryptography-36.0.2-cp36-abi3-manylinux_2_24_x86_64.whl (3.6 MB)
Requirement already satisfied: blinker>=1.9 in /usr/local/lib/python3.11/dist-packages (from Flask==3.1.0->-r requirements.txt (line 1)) (1.9.0)
Requirement already satisfied: itsdangerous>=2.2 in /usr/local/lib/python3.11/dist-packages (from Flask==3.1.0->-r requirements.txt (line 1)) (2.2.0)
Requirement already satisfied: Werkzeug>=3.1 in /usr/local/lib/python3.11/dist-packages (from Flask==3.1.0->-r requirements.txt (line 1)) (3.1.3)
Requirement already satisfied: click>=8.1.3 in /usr/local/lib/python3.11/dist-packages (from Flask==3.1.0->-r requirements.txt (line 1)) (8.2.1)
Requirement already satisfied: Jinja2>=3.1.2 in /usr/local/lib/python3.11/dist-packages (from Flask==3.1.0->-r requirements.txt (line 1)) (3.1.6)
Requirement already satisfied: greenlet>=1 in /usr/local/lib/python3.11/dist-packages (from SQLAlchemy==2.0.40->-r requirements.txt (line 4)) (3.2.2)
Requirement already satisfied: typing-extensions>=4.6.0 in /usr/local/lib/python3.11/dist-packages (from SQLAlchemy==2.0.40->-r requirements.txt (line 4)) (4.13.2)
Requirement already satisfied: cffi>=1.12 in /usr/local/lib/python3.11/dist-packages (from cryptography==36.0.2->-r requirements.txt (line 5)) (1.17.1)
Requirement already satisfied: pycparser in /usr/local/lib/python3.11/dist-packages (from cffi>=1.12->cryptography==36.0.2->-r requirements.txt (line 5)) (2.22)
Requirement already satisfied: MarkupSafe>=2.0 in /usr/local/lib/python3.11/dist-packages (from Jinja2>=3.1.2->Flask==3.1.0->-r requirements.txt (line 1)) (3.0.2)
Installing collected packages: SQLAlchemy, PyMySQL, Flask, cryptography, Flask-SQLAlchemy
  Attempting uninstall: Flask
    Found existing installation: Flask 3.1.1
    Uninstalling Flask-3.1.1:
      Successfully uninstalled Flask-3.1.1
  Attempting uninstall: cryptography
    Found existing installation: cryptography 45.0.3
    Uninstalling cryptography-45.0.3:
      Successfully uninstalled cryptography-45.0.3
Successfully installed Flask-3.1.0 Flask-SQLAlchemy-3.1.1 PyMySQL-1.1.1 SQLAlchemy-2.0.40 cryptography-36.0.2
3. Run development server: 

## Features
- RESTful API for employee and shift management
- Authentication and authorization
- Database models for businesses, employees, and schedules
- Customizable shift types

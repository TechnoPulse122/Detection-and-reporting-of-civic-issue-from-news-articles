# Detection and Reporting of Civic Issues from News Articles

## 👩‍💻 Project Information

**Project Title:** Detection and Reporting of Civic Issues from News Articles

**Project Type:** Academic Major Project

**Institution:** Guru Nanak Dev Engineering College, Ludhiana

**Project Supervisor:** Dr. Parminder Singh

**Project Team:**
- Jiya Kumari
- Asha Rani
- Divya



---

## 📌 Project Overview

Detection and Reporting of Civic Issues from News Articles is an AI-powered web-based system designed to automatically identify civic problems reported through online news articles and social media platforms.

The system collects information from multiple online sources, processes the collected data using Natural Language Processing (NLP), and uses a Large Language Model (LLM) to identify and classify relevant civic issues.

It extracts important information such as the issue description, locality, zone, severity, and associated department. The processed information is stored in a MySQL database and displayed through an interactive web dashboard.

The system also generates and sends automated email reports to the concerned departments to improve communication and support timely action on civic problems in Ludhiana.

---
## 🎯 Objectives

- To extract and analyse news articles  related to a particular city, from multilingual newspapers and  social media sources.
- To filter and classify news articles related to infrastructure, traffic, health, and other civic issues faced by the public.
- To develop a system to report filtered issues to the concerned department along with news article details.

---
## ✨ Key Features

### 1. Automated Data Collection
- Collects articles from multiple online news sources.
- Extracts relevant information using web scraping.
- Supports selected social media sources for civic-related updates.

### 2. NLP-Based Preprocessing
- Processes raw collected articles.
- Filters irrelevant and general news.
- Identifies potential civic-related information.
- Prevents unnecessary reprocessing of previously processed articles.

### 3. AI-Powered Issue Classification
- Uses a Large Language Model (LLM) through the Groq API.
- Identifies and categorizes civic issues.
- Extracts issue descriptions and relevant details.
- Associates issues with concerned departments and localities.
- Determines the severity of reported issues.

### 4. Interactive Dashboard
- Displays detected civic issues in a structured format.
- Provides information about issue categories, departments, localities, zones, and severity.
- Helps users monitor and analyze reported civic problems.

### 5. Automated Email Reporting
- Groups civic issues according to concerned departments and zones.
- Generates structured email reports.
- Sends reports to the corresponding departmental email addresses.
- Maintains email reporting logs to track sent and failed reports.

---

## 🔄 System Workflow

1. **Data Collection:** News articles are collected from online sources.

2. **Database Storage:** Raw collected articles are stored in the MySQL database.

3. **NLP Preprocessing:** Articles are cleaned, processed, and filtered to identify potential civic-related content.

4. **AI Classification:** Relevant articles are analyzed using an LLM to classify civic issues and extract important information.

5. **Issue Storage:** Classified civic issues are stored in the database with their associated details.

6. **Dashboard Visualization:** The detected issues are displayed through a Flask-based web dashboard.

7. **Automated Reporting:** Department-wise and zone-wise email reports are generated and sent to concerned authorities.

---

## 🛠️ Technologies Used

| Category | Technologies |
|---|---|
| Programming Language | Python |
| Backend Framework | Flask |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap 5 |
| Database | MySQL |
| Web Scraping | BeautifulSoup, Requests |
| Data Processing | Natural Language Processing (NLP) |
| AI / LLM | Groq API, GPT-OSS-20B |
| Data Visualization | Chart.js |
| Email Service | Python SMTP |
| Version Control | Git and GitHub |

---

## 🗄️ Database Design

The project uses MySQL for structured data storage and management.

The main database tables include:

- **articles:** Stores raw articles collected from news and social media sources.
- **processed_articles:** Stores preprocessed and filtered article records.
- **issues:** Stores classified civic issues and their extracted details.
- **email_log:** Maintains records of email reporting activities.

---

## 📂 Project Structure

```text
Civic-Issue-Detection/
│
├── main.py
├── run.py
├── db.py
├── scraper.py
├── nlp.py
├── classify.py
├── report.py
├── dash.py
│
├── templates/
│   └── alerts.html
│   └── analytics.html
│   └── dash.html
│   └── login.html
│   └── logs.html
│   └── reports.html
│
├── static/
│   ├── frames/
│   └── images/
├── .env.example
├── .gitignore
└── README.md
└──testEmail.py  
```
## ⚙️ Installation and Setup

### Prerequisites

Make sure the following are installed:

- Python 3.x
- MySQL Server / XAMPP
- Git
- A Groq API key

### Step 1: Clone the Repository

```bash
git clone https://github.com/TechnoPulse122/Detection-and-reporting-of-civic-issue-from-news-articles.git
```

### Step 2: Navigate to the Project Folder

```bash
cd Detection-and-reporting-of-civic-issue-from-news-articles
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the root directory and add the required credentials.

```env
dbuser=root
dbpassword=your_mysql_password

GROQ_API_KEY=your_groq_api_key

SENDER_EMAIL=your_email@gmail.com
APP_PASSWORD=your_gmail_app_password
```

Replace the example values with your actual credentials.

### Step 5: Configure MySQL

1. Start Apache and MySQL through XAMPP.
2. Create the database named `civic_db`.
3. Verify the database credentials in the `.env` file.
4. Ensure the required database tables are initialized by the project.

### Step 6: Run the Project

Execute the main pipeline using the project's orchestration script:

```bash
python main.py
```

To launch the dashboard separately, run:

```bash
python dash.py
```



---

## 🌍 Application Area

The system focuses on identifying and reporting civic issues in Ludhiana, Punjab.

Examples of civic issues include:

- Damaged roads and potholes.
- Garbage accumulation and sanitation problems.
- Water supply issues.
- Drainage and sewerage problems.
- Street lighting issues.
- Other public infrastructure-related concerns.

---

## 🚀 Future Scope
- Integration with additional news and social media platforms.
- Image-based civic issue detection.
- Integration with official municipal corporation systems.
- Improved analytics and reporting capabilities and logs.

## 📜 License

This project is developed for academic and educational purposes.
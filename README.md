## 📁 Project Structure  
  
```  
root/
├── docs/
│  
├── outputs/                  # Non existent until the first execution is finished
│   ├── client.log            # Log file  
│   ├── data.json             # Scraped data  
│   └── qa_report.txt         # Quality assurance results  
│  
├── src/
│   ├── __init__.py  
│   ├── data/
│   │   ├── __init__.py  
│   │   └── models.py         # Data models  
│   │  
│   ├── scraper/              # Scraping logic  
│   │   ├── __init__.py  
│   │   ├── quote_parser.py   # Parses quote content from pages  
│   │   ├── scraper_runner.py # Entry point to run the scraper logic  
│   │   └── utils/
│   │       ├── __init__.py  
│   │       ├── auth.py       # Authentication logic  
│   │       ├── constants.py  # Constant values used across scraper  
│   │       ├── scraper_utils.py # Helper functions for scraping  
│   │       └── setup_utils.py   # Initialization/setup helpers  
│   │  
│   └── tests/
│       ├── __init__.py  
│		├── schema.json       # JSON schema for data validation  
│       └── qa.py             # QA test script
│  
├── run_scraper.py            # Script to initiate scraper from CLI  
├── requirements.txt          # Python dependencies  
└── README.md                 # Project structure overview and run instructions  
```  
## 🏃‍♂️ How to run

> This project was developed using Python 3.11.11 so a similar version is recommended for running it.
> 
> It is also recommended to install dependencies and run the project in a virtual environment. The first time you run pip install <res of the command>, run it as suggested.

Open a terminal and standing on the root folder, run ```pip install --no-cache-dir --force-reinstall -r requirements.txt``` to install the project requirements and then follow with ```python run_scraper.py``` to run the scraper.
That will create the following files in the root/outputs folder:
- `data.json` containing all the scraped quotes, grouped by page.
- `qa_report.txt` containing the results of simple QA validation over the scraped content
- `client.log` file with information on important occurrences during the scraper execution

> If you wish to see real time logging to the terminal while running the scraper, go to `src.scraper.utils.setup_utils.py` and uncomment lines 24, 25 and 26

## 📋 Where to look
- Everything related to `Part 1: System Design Document` is present in the docs folder
- Everything related to `Part 2: Web Scraper Implementation` is present in the rest of the folders and root level files

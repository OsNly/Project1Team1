# Smart Expense Analyzer

An advanced personal expense tracker that extracts expenses from bank SMS messages or allows users to manually input them. Expenses are categorized, analyzed, and visualized to provide spending insights and advice.

## Features

- **Extract Expenses from SMS**: Upload your bank SMS CSV to automatically extract expenses based on merchant keywords.
- **Manual Expense Entry**: Input expenses manually with description, category, amount, and date.
- **Expense Summary**: Breakdown of spending by category.
- **Visualizations**: View total spending per category and spending trends over different months.
- **Spending Advice**: Personalized tips based on your spending habits.

## Visualizations

- **Spending by Category (Pie Chart)**: Shows total spending per category.
- **Spending Over Time (Bar Chart)**: Displays monthly categorized spending trends.


## Technologies Used

- **Python 3.10+**
- **Streamlit**: Web app interface.
- **Pandas**: Data manipulation and analysis.
- **Plotly**: Interactive visualizations.
- **Regex**: Extracting data from SMS.
- **Datetime**: Handling and formatting dates.

## Installation

1. Download files:

2. Create a virtual environment:
    ```bash
    python -m venv .venv
    ```

3. Activate the virtual environment:
    - On Windows:
        ```bash
        .\.venv\Scripts\activate
        ```
    - On Mac/Linux:
        ```bash
        source .venv/bin/activate
        ```

4. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## Running the App

To start the Streamlit app:
```bash
streamlit run app.py
```

## Files Overview

- **`app.py`**: Main Streamlit application file.
- **`requirements.txt`**: Python dependencies.
- **`sample_sms.csv`**: Sample SMS messages for testing and demonstration.



_This project was developed as part of the Data Science Bootcamp requirements._

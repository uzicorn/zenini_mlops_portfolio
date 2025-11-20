from fastapi.responses import HTMLResponse
from .. import engine
import pandas 
from os import path

def query_firewall(query: str):
    for suspicious in ["drop ", "delete ", "update ", "insert ", "truncate "]:
        if suspicious in query.lower():
            raise ValueError(f"Potentially unsafe SQL detected: {suspicious}")
    return query

from fastapi.responses import HTMLResponse
from html import escape

def errors(error, database_error=False, file_not_found_error=False, unsafe_sql=False) -> HTMLResponse:
    # Safely escape any raw error text
    safe_error = escape(str(error))

    error_title = "Unexpected Error"
    error_message = "An unexpected error occurred."

    if database_error:
        error_title = 'Database Error'
        error_message = f'Issue during <code>pandas.read_sql_query</code>: {safe_error}'
    elif file_not_found_error:
        error_title = 'File Not Found'
        error_message = f'Query file missing in <code>./webapp/sql/</code>: {safe_error}'
    elif unsafe_sql:
        error_title = 'Unsafe SQL Detected'
        error_message = safe_error

    html = f"""
    <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', sans-serif;
                    background-color: #f9f9f9;
                    padding: 2rem;
                }}
                .error-container {{
                    background: #fff3f3;
                    border-left: 6px solid #e53935;
                    padding: 1rem 1.5rem;
                    border-radius: 8px;
                    max-width: 70%;
                }}
                .error-title {{
                    font-size: 1.2rem;
                    font-weight: bold;
                    color: #b71c1c;
                    margin-bottom: 0.5rem;
                }}
                .error-message {{
                    color: #444;
                    white-space: pre-wrap;
                }}
            </style>
        </head>
        <body>
            <div class="error-container">
                <div class="error-title">{error_title}</div>
                <div class="error-message">{error_message}</div>
            </div>
        </body>
    </html>
    """
    return HTMLResponse(content=html, status_code=500)

    
def get_backend_data(query_name: str) -> HTMLResponse:
    """
    query_name: query name without .sql
    """
    curdir = path.dirname(__file__)

    # Read and check query
    try:
        with open(path.join(curdir, "sql", f"{query_name}.sql")) as q:
            query = q.read()
        query = query_firewall(query)

    except FileNotFoundError as e:
        return errors(error=e, file_not_found_error=True)
    except ValueError as e:
        return errors(error=e, unsafe_sql=True)

    # Execute query : Retrieve DataFrame
    try:
        df_data = pandas.read_sql_query(sql=query, con=engine)
    except Exception as e:
        return errors(error=e, database_error=True)

    # Convert df -> HTML 
    html_table = df_data.to_html(
        classes="dataframe", 
        border=0,
        justify="center"
    )

    # Construct HTML response
    html = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Query Result - {query_name}</title>
        <style>
            body {{
                font-family: 'Segoe UI', sans-serif;
                background-color: #f3f8f4;
                padding: 2rem;
                color: #2e4730;
            }}
            h1 {{
                color: #1b5e20;
                text-align: center;
            }}
            .refresh-btn {{
                display: inline-block;
                background-color: #2e7d32;
                color: white;
                border: none;
                padding: 0.5rem 1rem;
                border-radius: 6px;
                cursor: pointer;
                font-size: 1rem;
                margin-bottom: 1rem;
                transition: background 0.2s ease;
            }}
            .refresh-btn:hover {{
                background-color: #1b5e20;
            }}
            .table-container {{
                overflow-x: auto;
                overflow-y: hidden;
                max-width: 100%;
                border-radius: 8px;
                box-shadow: 0 1px 4px rgba(0,0,0,0.1);
                padding-bottom: 0.5rem;
                margin: auto;
            }}
            table.dataframe {{
                width: 100%;
                border: 1px solid #dededf;
                border-collapse: collapse;
                table-layout: auto;
            }}
            table.dataframe th {{
                border: 1px solid #dededf;
                background-color: #eceff1;
                color: #000000;
                padding: 5px;
                white-space: nowrap; 
            }}
            table.dataframe td {{
                border: 1px solid #dededf;
                background-color: #ffffff;
                color: #000000;
                padding: 5px;
                max-width: 200px;        
                overflow: hidden;                          
                white-space: nowrap; 
                }}
            table.dataframe td:hover {{
                overflow: visible;
                color: red;
                max-width: 100%;
                }}
            .footer {{
                margin-top: 1rem;
                text-align: center;
                font-size: 0.9rem;
                color: #4a4a4a;
            }}
        </style>
    </head>
    <body>
        <h1>Query: {query_name}</h1>
        <div style="text-align:center;">
            <button class="refresh-btn" onClick="window.location.reload();">↻ Refresh Page</button>
        </div>
        <div class="table-container">
            {html_table}
        </div>
        <div class="footer">Rendered directly from backend • {df_data.shape[0]} rows</div>
    </body>
    </html>
    """

    return HTMLResponse(content=html, status_code=200)

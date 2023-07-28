import tkinter as tk
from tkinter import ttk
import spacy
from sqlalchemy import create_engine, MetaData, Table, select, func, Date, cast
import dateparser

# Initialize spacy language model
nlp = spacy.load("en_core_web_sm")

# Create SQLAlchemy engine and connect to the database
engine = create_engine('mysql://root:rohan@localhost/school')
metadata = MetaData(bind=engine)
metadata.reflect()
connection = engine.connect()

# Get all the foreign key relationships
foreign_keys = {}
for table_name, table in metadata.tables.items():
    for fk in table.foreign_keys:
        if fk.column.table.name not in foreign_keys:
            foreign_keys[fk.column.table.name] = {}
        foreign_keys[fk.column.table.name][table_name] = fk.column.name

# Function to handle user query conversion and display the result
def handle_query_conversion():
    # Clear previous conversion and result (if any)
    query_conversion.delete(1.0, tk.END)
    query_result.delete(1.0, tk.END)

    # Get user input
    user_input = input_entry.get()

    # Get selected tables
    selected_tables = [table for table, var in table_vars.items() if var.get() == 1]

    # Check if all tables are selected
    all_tables_selected = len(selected_tables) == len(table_vars)

    if not user_input and all_tables_selected:
        # All checkboxes are selected and user input is empty,
        # execute the query with all columns from all tables
        query = convert_to_sql_query_all_columns(selected_tables)
    else:
        # Convert user input to SQL query with date filter
        query = convert_to_sql_query_with_date(user_input, selected_tables)

    if query is not None:
        # Display query conversion
        query_conversion.insert(tk.END, str(query))

        # Execute the SQL query
        result = connection.execute(query)
        rows = result.fetchall()

        # Display the result in the query result textbox
        for row in rows:
            query_result.insert(tk.END, str(row) + "\n")
    else:
        # Display an error message if the query is not valid
        query_conversion.insert(tk.END, "Invalid query. Please check your input.")

# Function to convert user input and selected tables to SQL query with date filter
def convert_to_sql_query_with_date(user_input, selected_tables):
    doc = nlp(user_input)
    tables = [Table(table, metadata, autoload=True, autoload_with=engine) for table in selected_tables]
    table_aliases = {table.name: table.alias() for table in tables}

    if tables:
        # Start the query by selecting all columns from all tables
        columns = [table_alias for table_alias in table_aliases.values()]
        query = select(columns)

        # Join the remaining tables using defined foreign key relationships
        for i in range(1, len(tables)):
            if tables[i].name in foreign_keys and table_aliases[tables[i].name].name in foreign_keys[tables[i].name]:
                fk_column_name = foreign_keys[tables[i].name][table_aliases[tables[i].name].name]
                join_condition = table_aliases[tables[i].name].c[fk_column_name] == table_aliases[table_aliases[tables[i].name].name].c[fk_column_name]
                query = query.join(table_aliases[tables[i].name], join_condition)

        date_found = None

        # Extract the date from the input text using dateparser
        for token in doc:
            if token.ent_type_ == "DATE":
                parsed_date = dateparser.parse(token.text)
                if parsed_date:
                    date_found = parsed_date.date()
                    break

        # Add date filter to the query
        if date_found:
            query = query.where(cast(func.DATE(table_aliases[tables[0].name].c.salesdate), Date) == date_found)

        return query

    return None

# Function to convert user input and selected tables to SQL query with all columns
def convert_to_sql_query_all_columns(selected_tables):
    # Start the query by selecting all columns from all tables
    tables = [Table(table, metadata, autoload=True, autoload_with=engine) for table in selected_tables]
    columns = [table.c for table in tables]

    query = select(columns)

    # Join the remaining tables using defined foreign key relationships
    for i in range(1, len(tables)):
        if tables[i].name in foreign_keys and tables[i].name in foreign_keys[tables[i].name]:
            fk_column_name = foreign_keys[tables[i].name][tables[i].name]
            join_condition = tables[i].c[fk_column_name] == tables[foreign_keys[tables[i].name][tables[i].name]].c[fk_column_name]
            query = query.join(tables[i], join_condition)

    return query

# Create the main application window
window = tk.Tk()
window.title("SQL Query Converter")
window.geometry("800x400")

# Create a frame for tables
tables_frame = ttk.Frame(window)
tables_frame.pack(pady=10)

# Get the table names from the database
table_names = engine.table_names()

# Create a dictionary to hold table variables
table_vars = {}

# Create checkboxes for tables
for table in table_names:
    var = tk.IntVar()
    table_vars[table] = var
    checkbox = ttk.Checkbutton(tables_frame, text=table, variable=var)
    checkbox.pack(side=tk.LEFT)

# Create an input box for user query
input_entry = ttk.Entry(window)
input_entry.pack(pady=10)

# Create a button to convert user query
convert_button = ttk.Button(window, text="Convert", command=handle_query_conversion)
convert_button.pack()

# Create a frame to display the converted query
query_conversion = tk.Text(window, width=70, height=5)
query_conversion.pack(pady=10)

# Create a text box to display the query result
query_result = tk.Text(window, width=110, height=10)
query_result.pack(pady=10)

# Run the main event loop
window.mainloop()

# Close the database connection on application exit
connection.close()

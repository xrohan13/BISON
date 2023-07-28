import tkinter as tk
from tkinter import ttk
import spacy
from sqlalchemy import create_engine, MetaData, Table, select, cast, Date, literal_column
import datetime
import dateparser

# Connect to the MySQL database
engine = create_engine('mysql://root:rohan@localhost/emp')
connection = engine.connect()

# Load the spaCy English language model
nlp = spacy.load('en_core_web_sm')

# Create a Tkinter window
window = tk.Tk()
window.title("SQL Query Converter")

# Create a frame for table selection
table_frame = ttk.Frame(window)
table_frame.pack(pady=10)

# Create a frame for user input and query conversion
input_frame = ttk.Frame(window)
input_frame.pack(pady=10)

# Create a frame for result display
result_frame = ttk.Frame(window)
result_frame.pack(pady=10)

# Retrieve the table names from the database
metadata = MetaData()
metadata.reflect(bind=engine)
table_names = list(metadata.tables.keys())

# Selected table
selected_table = tk.StringVar()

# Selected tables
selected_tables = []

# Create a function to handle table selection
def handle_table_selection(event):
    selected_table.set(table_dropdown.get())

# Create a dropdown menu for table selection
table_dropdown = ttk.Combobox(table_frame, values=table_names)
table_dropdown.grid(row=0, column=0, padx=5, pady=2)
table_dropdown.bind("<<ComboboxSelected>>", handle_table_selection)

# Create a function to handle user query conversion
def handle_query_conversion():
    # Clear previous conversion and result (if any)
    query_conversion.delete(1.0, tk.END)
    query_result.delete(1.0, tk.END)

    # Get user input
    user_input = input_entry.get()

    # Convert user input to SQL query
    query, date_found = convert_to_sql_query(user_input, selected_table.get())

    if query is not None:
        # Display query conversion
        query_conversion.insert(tk.END, str(query))

        # Execute the SQL query
        if date_found:
            result = connection.execute(query)
            rows = result.fetchall()

            # Display the result in the query result textbox
            for row in rows:
                query_result.insert(tk.END, str(row) + "\n")
        else:
            query_result.insert(tk.END, "Date not found in the input.")
    else:
        # Display an error message if the query is not valid
        query_conversion.insert(tk.END, "Invalid query. Please check your input.")


# Convert user input to SQL query
def convert_to_sql_query(user_input, table_name):
    doc = nlp(user_input)
    metadata = MetaData()
    metadata.reflect(bind=engine)
    selected_table_object = Table(table_name, metadata, autoload=True, autoload_with=engine)

    if selected_table_object is not None:
        query = select([selected_table_object])
        date_found = False

        # Extract the date from the input text using dateparser
        for token in doc:
            if token.ent_type_ == "DATE":
                parsed_date = dateparser.parse(token.text)
                if parsed_date:
                    query_date = parsed_date.date()
                    query = query.where(cast(selected_table_object.c.salesdate, Date) == query_date)
                    date_found = True
                    break

        return query, date_found

    return None, None

# Convert user input to SQL query for all table values
def convert_to_sql_query_all_tables():
    selected_table_objects = [Table(table_name, metadata, autoload=True, autoload_with=engine) for table_name in selected_tables]

    if selected_table_objects:
        query = select()

        for table_object in selected_table_objects:
            query = query.select_from(table_object)

        return query

    return None

# Create an entry for user input
input_entry = ttk.Entry(input_frame)
input_entry.pack(side=tk.LEFT, padx=5)

# Create a button to convert user input to SQL query
conversion_button = ttk.Button(input_frame, text="Convert", command=handle_query_conversion)
conversion_button.pack(side=tk.LEFT, padx=5)

# Create a textbox to display query conversion
query_conversion = tk.Text(input_frame, width=40, height=5)
query_conversion.pack(pady=5)

# Create a textbox to display query result
query_result = tk.Text(result_frame, width=40, height=10)
query_result.pack(pady=5)

# Start the Tk
window.mainloop()
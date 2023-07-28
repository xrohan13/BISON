import datetime
import tkinter as tk
from tkinter import ttk
import spacy
from sqlalchemy import create_engine, MetaData, Table, select, cast, Date

# Connect to the MySQL database
engine = create_engine('mysql://root:rohan@localhost/emp')
connection = engine.connect()

# Load the spaCy English language model
nlp = spacy.load('en_core_web_sm')

# Create a Tkinter window
window = tk.Tk()
window.title("Table Viewer")

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

# Create a dropdown menu for table selection
selected_table = tk.StringVar()
table_dropdown = ttk.Combobox(table_frame, textvariable=selected_table, values=table_names)
table_dropdown.grid(row=0, column=0, padx=5, pady=2)
table_dropdown.set("Select Table")


# Create a function to handle user query conversion
def handle_query_conversion():
    # Clear previous result and query conversion (if any)
    query_result.delete(1.0, tk.END)
    query_conversion.delete(1.0, tk.END)

    # Get user input
    user_input = input_entry.get()

    # Convert user input to SQL query
    query, executed_query = convert_to_sql_query(user_input, selected_table.get())

    # Display the SQL query conversion
    query_conversion.insert(tk.END, str(query))

    # Display the executed SQL query
    query_result.insert(tk.END, "Executed Query:\n")
    query_result.insert(tk.END, str(executed_query))

def convert_to_sql_query(user_input, table_name):
    doc = nlp(user_input)
    metadata = MetaData()
    metadata.reflect(bind=engine)

    # Check if the selected table exists in the database
    if table_name in metadata.tables:
        selected_table_object = Table(table_name, metadata, autoload=True, autoload_with=engine)
    else:
        return None, None

    query = select([selected_table_object])

    columns_selected = False  # Flag to check if any columns are selected

    for token in doc:
        if token.pos == spacy.symbols.NOUN:
            if token.text.lower() == "select":
                pass  # Do nothing as we are already selecting all columns with '*'
            elif token.text.lower() == "from":
                pass  # Skip 'FROM' keyword
            else:
                columns = [selected_table_object.c[col_name] for col_name in selected_table_object.columns.keys() if token.text.lower() in col_name.lower()]
                if columns:
                    query = query.with_only_columns(columns)
                    columns_selected = True

    # If no columns are selected, add the wildcard '*' to the query
    if not columns_selected:
        query = query.with_only_columns([selected_table_object])

    # Filter for the current date
    today_date = datetime.date.today()
    query = query.where(cast(selected_table_object.c.salesdate, Date) == str(today_date))  # Convert to string here

    # Compile the SQL query for display
    executed_query = query.compile(compile_kwargs={"literal_binds": True})

    return query, executed_query




# Create an entry for user input
input_entry = ttk.Entry(input_frame)
input_entry.pack(side=tk.LEFT, padx=5)

# Create a button to convert user input to SQL query
conversion_button = ttk.Button(input_frame, text="Convert", command=handle_query_conversion)
conversion_button.pack(side=tk.LEFT, padx=5)

def handle_query_execution():
    # Clear previous result (if any)
    query_result.delete(1.0, tk.END)

    # Get query conversion
    query, executed_query = convert_to_sql_query(input_entry.get(), selected_table.get())

    # Execute the SQL query
    result = connection.execute(query)

    # Display the executed SQL query
    query_result.insert(tk.END, "Executed SQL Query:\n")
    query_result.insert(tk.END, str(executed_query) + "\n\n")

    # Display the result in the query result textbox
    query_result.insert(tk.END, "Result:\n")
    for row in result.fetchall():
        query_result.insert(tk.END, str(row) + "\n")

# Create a textbox to display query conversion
query_conversion = tk.Text(input_frame, width=40, height=5)
query_conversion.pack(pady=5)

# Create a textbox to display query result
query_result = tk.Text(result_frame, width=40, height=10)
query_result.pack(pady=5)

execute_button = ttk.Button(window, text="Execute Query", command=handle_query_execution)
execute_button.pack(pady=10)
# Start the Tkinter event loop
window.mainloop()

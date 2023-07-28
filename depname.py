import tkinter as tk
from tkinter import ttk
from sqlalchemy import create_engine, MetaData, Table, select

# Connect to the MySQL database
engine = create_engine('mysql://root:rohan@localhost/emp')
connection = engine.connect()

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

# Selected tables
selected_tables = []

# Create a function to handle user query conversion
def handle_query_conversion():
    # Clear previous conversion and result (if any)
    query_conversion.delete(1.0, tk.END)

    # Get user input
    user_input = "SELECT s.salesamt FROM emp.employees e JOIN emp.dept_emp de ON e.emp_id = de.empid JOIN emp.sales s ON e.emp_id = s.emppid WHERE de.depname = 'IT';"

    # Replace depname with user input
    user_input = user_input.replace("'IT'", f"'{department_entry.get()}'")

    # Display query conversion
    query_conversion.insert(tk.END, user_input)

# Create dropdown menus for table selection
table_dropdowns = []
for i, table_name in enumerate(table_names):
    var = tk.IntVar()
    checkbox = ttk.Checkbutton(table_frame, text=table_name, variable=var, command=lambda table=table_name: toggle_table(table))
    checkbox.grid(row=i, column=0, padx=5, pady=2)
    table_dropdowns.append(checkbox)

# Toggle table selection
def toggle_table(table):
    if table in selected_tables:
        selected_tables.remove(table)
    else:
        selected_tables.append(table)

# Create an entry for user input
department_label = ttk.Label(input_frame, text="Department Name:")
department_label.pack(side=tk.LEFT, padx=5)
department_entry = ttk.Entry(input_frame)
department_entry.pack(side=tk.LEFT, padx=5)

# Create a button to convert user input to SQL query
conversion_button = ttk.Button(input_frame, text="Convert", command=handle_query_conversion)
conversion_button.pack(side=tk.LEFT, padx=5)

# Create a textbox to display query conversion
query_conversion = tk.Text(input_frame, width=40, height=5)
query_conversion.pack(pady=5)

# Create a textbox to display query result
query_result = tk.Text(result_frame, width=40, height=10)
query_result.pack(pady=5)

def handle_query_execution():
    # Clear previous result (if any)
    query_result.delete(1.0, tk.END)

    # Get query conversion
    query = query_conversion.get(1.0, tk.END)

    # Execute the SQL query
    result = connection.execute(query)
    rows = result.fetchall()

    # Display the result in the query result textbox
    for row in rows:
        query_result.insert(tk.END, str(row) + "\n")

# Create a button to execute the SQL query
execute_button = ttk.Button(window, text="Execute Query", command=handle_query_execution)
execute_button.pack(pady=10)
# Start the Tkinter event loop
window.mainloop()

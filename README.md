Semantic Column Classifier

This project provides a small toolset for identifying the type of data stored in a CSV column and parsing it into a structured format. It also exposes these features through a lightweight MCP server so they can be called programmatically.

The system supports:

Detecting the semantic type of a column

Parsing company names and phone numbers

Returning results through an MCP-compatible interface

Features
1. Column Classification

predict.py predicts the type of a given column using a set of rules based on:

Phone number formats

Date parsing

Country list matching

Legal suffix detection for company names

Supported labels:

PhoneNumber

CompanyName

Country

Date

Other

2. Column Parsing

parser.py automatically selects the most suitable column and parses it:

Phone numbers → extracts country code (when possible) and digits

Company names → separates the name from the legal entity suffix

The output is written to:

output.csv

3. MCP Server

The server in mcp_server/server.py exposes three tools:

Tool Name	Description
list_files	Lists CSV files in the data/ directory
column_prediction	Runs the classifier on a selected column
parse_file	Parses the file and produces output.csv

The interface follows a simple JSON-over-stdin/stdout pattern as described in the MCP specification.

Project Structure

<img width="564" height="794" alt="image" src="https://github.com/user-attachments/assets/e16ed139-2648-43f0-aca7-674ec3de6b2a" />

How to Use
Predict a column type
python predict.py --input data/phone.csv --column number

Parse a file
python parser.py --input data/phone.csv

Run the MCP server
python mcp_server/server.py


Then send JSON requests such as:

{"id":"1","tool":"list_files","args":{}}

Notes

The classification and parsing logic is rule-based for consistency and ease of inspection.

All outputs are deterministic and do not rely on external services or trained models.



https://github.com/user-attachments/assets/f0f4362d-e879-47f2-982f-8b3b7de375c8

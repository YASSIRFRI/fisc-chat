# PDF Law Preprocessor

This project is designed to preprocess law documents in PDF format. It extracts text from the documents, maps articles to their corresponding text, and handles noise, tables, and preserves the structure and semantics of the original document.

## Project Structure




```
pdf-law-preprocessor
├── src
│   ├── __init__.py
│   ├── main.py
│   ├── preprocessor
│   │   ├── __init__.py
│   │   ├── extractor.py
│   │   ├── cleaner.py
│   │   └── mapper.py
│   ├── parsers
│   │   ├── __init__.py
│   │   ├── text_parser.py
│   │   ├── table_parser.py
│   │   └── structure_parser.py
│   └── utils
│       ├── __init__.py
│       └── helpers.py
├── tests
│   ├── __init__.py
│   ├── test_extractor.py
│   ├── test_cleaner.py
│   └── test_mapper.py
├── data
│   ├── input
│   └── output
├── config
│   └── settings.py
├── requirements.txt
├── setup.py
└── README.md
```

## Installation

To install the required dependencies, run:

```
pip install -r requirements.txt
```

## Usage

To run the preprocessor, execute the following command:

```
python src/main.py
```

Make sure to place your input PDF files in the `data/input` directory. The processed output will be saved in the `data/output` directory.

## Features

- **Text Extraction**: Extracts raw text from PDF documents while handling noise and irrelevant content.
- **Text Cleaning**: Cleans the extracted text to remove formatting issues and noise, preserving the document's structure.
- **Article Mapping**: Maps articles to their corresponding text, ensuring the semantic structure is maintained.
- **Table Handling**: Converts tables into structured lines of text, preserving data integrity.
- **Document Structure Analysis**: Analyzes the overall structure of the document to maintain the hierarchy of articles.

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any suggestions or improvements.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.
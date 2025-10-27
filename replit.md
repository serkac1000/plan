# Proteus Connection Editor

## Overview
A Flask web application for editing connections in Proteus electronic circuit design files (.pdsprj). This tool allows users to:
- Upload Proteus project files
- Parse and visualize circuit components
- Create and edit connections between components
- Generate Proteus-compatible connection files and scripts

## Project Status
- **Current State**: Fully functional Flask web application
- **Last Updated**: October 27, 2025
- **Import Source**: GitHub project import

## Technology Stack
- **Framework**: Flask 3.1.2
- **Language**: Python 3.11
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Key Dependencies**: 
  - flask
  - werkzeug

## Project Structure
```
/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── index.html        # Arduino code generator page
│   ├── output.html       # Output display page
│   └── proteus.html      # Main Proteus connection editor
├── uploads/              # Uploaded Proteus files and generated outputs
├── .gitignore            # Git ignore rules
└── replit.md             # This file
```

## Key Features

### 1. Proteus File Parser
- Supports ZIP-based Proteus files (Proteus 8+)
- Handles legacy XML and binary formats
- Extracts component information and pin configurations
- File analysis and version detection

### 2. Connection Editor
- Visual component display
- Interactive connection creation
- Pin-to-pin connection mapping
- Support for multiple component types (ICs, resistors, LEDs, switches, power rails)

### 3. Export Formats
- **Proteus-compatible file**: Safe copy of original with connections
- **Netlist (.net)**: Standard netlist format
- **Script (.scr)**: Proteus script for automatic wiring
- **Wiring guide (.txt)**: Human-readable connection instructions

### 4. Arduino Code Generator
- Secondary feature for generating Arduino/ESP32 code
- Motor control integration
- Sensor support
- Communication protocols (Bluetooth, WiFi, Serial)

## Setup & Configuration

### Development Server
- **Host**: 0.0.0.0 (configured for Replit)
- **Port**: 5000
- **Debug Mode**: Enabled in development

### Workflow
- Name: Server
- Command: `python app.py`
- Output: webview on port 5000

## Usage

### Main Application (Proteus Editor)
1. Navigate to the home page (/)
2. Upload a .pdsprj file
3. View parsed components
4. Create connections between pins
5. Generate and download connection files

### Arduino Code Generator
1. Navigate to /proteus
2. Fill in project parameters
3. Generate requirements and code

## File Handling
- Upload folder: `uploads/`
- Max file size: 16MB
- Supported formats: .pdsprj (Proteus project files)
- Generated files are timestamped to avoid conflicts

## Recent Changes
- October 27, 2025: Initial Replit environment setup
  - Configured server to use 0.0.0.0 for Replit compatibility
  - Fixed LSP error for file_info variable initialization
  - Added comprehensive .gitignore
  - Set up workflow for automatic server restart

## User Preferences
None recorded yet.

## Notes
- The application uses demo components if parsing fails
- All connections are safe - original files are never modified directly
- Generated scripts may fail if component names don't match exactly in Proteus

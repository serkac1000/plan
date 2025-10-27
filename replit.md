# Proteus Connection Editor

## Overview
A Flask web application for editing connections in Proteus electronic circuit design files (.pdsprj). This tool allows users to:
- Upload Proteus project files
- Parse and visualize circuit components
- Create and edit connections between components
- Generate Proteus-compatible connection files and scripts with **Wire Autorouter** support

## Project Status
- **Current State**: Fully functional Flask web application with Wire Autorouter integration
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
- Extracts component information and pinsn configurations
- File analysis and version detection

### 2. Connection Editor
- Visual component display
- Interactive connection creation
- Pin-to-pin connection mapping
- Support for multiple component types (ICs, resistors, LEDs, switches, power rails)

### 3. Export Formats
- **Proteus-compatible file**: Safe copy of original with connections
- **Netlist (.net)**: Standard netlist format
- **Script (.scr)**: Proteus script with Wire Autorouter commands for automatic wiring
- **Wiring guide (.txt)**: Human-readable connection instructions (backup/manual method)

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

## How to Use the Autorouter Script in Proteus

The generated `.scr` script file uses Proteus **Wire Autorouter** to automatically route all connections. This is the **fastest and recommended method**.

### Method 1: Script Editor (Recommended)

1. **Open your ORIGINAL Proteus project** (.pdsprj file)
   - Do NOT open the "connected_proteus_*.pdsprj" file
   - Use your original, unmodified project

2. **Download the Script file**
   - After saving connections, download the `connect_script_YYYYMMDD_HHMMSS.scr` file

3. **Open Script Editor in Proteus**
   - Go to: **Tools → Plugins → Script Editor**
   - Or use the toolbar button if available

4. **Load the Script**
   - Click **File → Open** in the Script Editor
   - Browse to your downloaded `.scr` file
   - OR copy and paste the script contents directly into the editor

5. **Run the Script**
   - Click the **Run** button (▶) in the Script Editor
   - The Wire Autorouter will automatically:
     - Connect all specified pins
     - Route wires intelligently
     - Avoid obstacles and optimize paths

6. **Verify and Save**
   - Check that all connections appear correctly
   - Manually adjust any routes if needed
   - Save your Proteus project

### Method 2: Command Line (Alternative)

1. **Open your ORIGINAL Proteus project**

2. **Open Command Line**
   - Press **F12** in Proteus ISIS
   - The command line appears at the bottom

3. **Execute Script**
   - Type: `SCRIPT "C:\path\to\connect_script_YYYYMMDD_HHMMSS.scr"`
   - Replace the path with your actual script location
   - Press **Enter**

4. **Autorouter Runs**
   - Watch as connections are created automatically
   - The command line shows progress messages

5. **Save your project**

### Troubleshooting

**If autorouter fails:**
- Verify component reference designators match (e.g., IC1, R1, D1)
- Check that pin names/numbers are correct
- Ensure Wire Autorouter plugin is enabled in Proteus
- Fall back to the manual wiring guide (.txt file)

**Common Issues:**
- "Component not found" → Component ID mismatch between script and schematic
- "Pin not found" → Pin name/number doesn't match component definition
- Script doesn't run → Check file path is correct (no spaces, use quotes)

### What the Autorouter Script Does

The script contains commands like:
```
AUTOROUTE ON
WIRE FROM IC1.D13 TO D1.A
WIRE FROM R1.1 TO D1.K
AUTOROUTE OPTIMIZE
```

These commands:
1. Enable Wire Autorouter mode
2. Create connections between specified pins
3. Automatically route wires around components
4. Optimize routing for minimal crossovers
5. Complete all wiring without manual intervention

### Arduino Code Generator
1. Navigate to /proteus
2. Fill in project parameters
3. Generate requirements and code

## File Handling
- Upload folder: `uploads/`
- Max file size: 16MB
- Supported formats: .pdsprj (Proteus project files))
- Generated files are timestamped to avoid conflicts

## Recent Changes
- October 27, 2025: Wire Autorouter Integration
  - Added Wire Autorouter support to generated scripts
  - Updated script generation with AUTOROUTE commands
  - Enhanced documentation for autorouter usage
  - Added comprehensive troubleshooting guide

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
- **Wire Autorouter** handles all routing automatically - no manual wiring needed!
- Scripts include error checking for missing components/pins
- Always use your ORIGINAL .pdsprj file when running scripts
- The autorouter optimizes wire paths for best routing results fail if component names don't match exactly in Proteus

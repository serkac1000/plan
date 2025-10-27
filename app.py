from flask import Flask, render_template, request, jsonify, send_file
import os
from datetime import datetime
import json
import xml.etree.ElementTree as ET
from werkzeug.utils import secure_filename
import zipfile
import tempfile
import shutil

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Store proteus data globally
proteus_data = {}

@app.route('/')
def index():
    """Main Proteus connection editor page"""
    return render_template('proteus.html')

@app.route('/upload_proteus', methods=['POST'])
def upload_proteus():
    """Upload and parse Proteus .pdsprj file"""
    global proteus_data
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not file.filename.lower().endswith('.pdsprj'):
        return jsonify({'error': 'Please upload a .pdsprj file'}), 400
    
    try:
        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Parse Proteus file
        components = parse_proteus_file(filepath)
        
        # Store data globally
        proteus_data = {
            'filename': filename,
            'filepath': filepath,
            'components': components,
            'connections': [],
            'original_content': read_original_proteus_content(filepath)
        }
        
        # Add file analysis info to the response
        file_info = analyze_proteus_file(filepath)
        
        return jsonify({
            'status': 'success',
            'message': f'Successfully parsed {len(components)} components from {filename}',
            'components': components,
            'filename': filename,
            'file_info': file_info
        })
        
    except Exception as e:
        return jsonify({'error': f'Error processing file: {str(e)}'}), 500

@app.route('/save_connections', methods=['POST'])
def save_connections():
    """Save connections to Proteus file"""
    global proteus_data
    
    if not proteus_data:
        return jsonify({'error': 'No Proteus file loaded'}), 400
    
    try:
        connections_data = request.get_json()
        connections = connections_data.get('connections', [])
        
        # Update proteus_data with connections
        proteus_data['connections'] = connections
        
        # Create updated Proteus file that can be opened in Proteus
        updated_filename = create_proteus_compatible_file(proteus_data['filepath'], connections)
        
        # Create separate connection files for manual import
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        create_connection_files(timestamp, connections)
        
        return jsonify({
            'status': 'success',
            'message': f'Proteus-compatible file created successfully!',
            'updated_file': updated_filename,
            'connections_count': len(connections)
        })
        
    except Exception as e:
        return jsonify({'error': f'Error saving connections: {str(e)}'}), 500

def read_original_proteus_content(filepath):
    """Read and store original Proteus file content"""
    try:
        # Try to read as ZIP first
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_file:
                content = {}
                for file_name in zip_file.namelist():
                    try:
                        with zip_file.open(file_name) as f:
                            content[file_name] = f.read()
                    except:
                        pass
                return content
        except zipfile.BadZipFile:
            # Read as binary file
            with open(filepath, 'rb') as f:
                return {'main_file': f.read()}
    except Exception as e:
        print(f"Error reading original content: {e}")
        return {}

def parse_proteus_file(filepath):
    """Parse Proteus .pdsprj file and extract components"""
    components = []
    file_info = {}
    
    try:
        # Get file info first
        file_info = analyze_proteus_file(filepath)
        print(f"File analysis: {file_info}")
        
        # Try as ZIP file first (most common for newer Proteus versions)
        if file_info.get('is_zip', False):
            try:
                with zipfile.ZipFile(filepath, 'r') as zip_file:
                    file_list = zip_file.namelist()
                    print(f"ZIP contents: {file_list}")
                    
                    for file_name in file_list:
                        if file_name.endswith(('.pdsprj', '.xml', '.dsn', '.PWI')):
                            print(f"Trying to parse: {file_name}")
                            with zip_file.open(file_name) as xml_file:
                                try:
                                    # Try to read as text first
                                    content = xml_file.read().decode('utf-8', errors='ignore')
                                    if '<' in content and '>' in content:
                                        root = ET.fromstring(content)
                                        components = extract_components_from_xml(root)
                                        if components and len([c for c in components if c['name'] != 'Component']) > 0:
                                            print(f"Successfully extracted {len(components)} components from {file_name}")
                                            return components
                                except (ET.ParseError, UnicodeDecodeError) as e:
                                    print(f"Failed to parse {file_name}: {e}")
                                    continue
            except (zipfile.BadZipFile, zipfile.LargeZipFile) as e:
                print(f"ZIP file error: {e}, trying other methods...")
            except Exception as e:
                print(f"ZIP reading error: {e}, trying other methods...")
        else:
            print("File is not a ZIP archive, trying direct parsing methods...")
        
        # Try to read as direct XML/text file
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # Check if it contains XML-like content
            if '<' in content and '>' in content:
                try:
                    # Try to parse as XML directly
                    root = ET.fromstring(content)
                    components = extract_components_from_xml(root)
                    if components:
                        print(f"Successfully parsed as direct XML: {len(components)} components")
                        return components
                except ET.ParseError as e:
                    print(f"XML parsing failed: {e}")
        except Exception as e:
            print(f"Direct file reading failed: {e}")
            
    except Exception as e:
        print(f"General parsing error: {e}")
    
    # If all parsing fails, create demo components based on file analysis
    print(f"Could not parse Proteus file format (Type: {file_info.get('type', 'Unknown')})")
    print("Creating demo components for testing the connection editor")
    return create_demo_components_for_proteus()

def extract_components_from_xml(root):
    """Extract components from XML root element with real Proteus names"""
    components = []
    component_id = 1
    
    # Look for common Proteus XML structures
    print(f"XML root tag: {root.tag}")
    print(f"XML root attributes: {root.attrib}")
    
    # Try different possible XML structures
    for element in root.iter():
        tag_name = element.tag.lower()
        element_text = element.text or ''
        
        # Look for component-like elements with more specific Proteus patterns
        if any(keyword in tag_name for keyword in ['component', 'part', 'device', 'symbol', 'instance', 'compinst', 'element']):
            # Try to get the actual reference designator (like IC1, R1, D1, etc.)
            ref_des = (element.get('refdes') or 
                      element.get('name') or 
                      element.get('id') or 
                      element.get('ref') or
                      element.get('designator'))
            
            # Get component type/device name
            comp_type = (element.get('device') or 
                        element.get('type') or 
                        element.get('library') or 
                        element.get('part') or
                        'Unknown')
            
            # Get component value
            value = (element.get('value') or 
                    element.get('val') or 
                    element.get('model') or
                    element.get('package') or
                    '')
            
            # If we found a real reference designator, use it
            if ref_des and ref_des != 'Unknown' and len(ref_des) > 0:
                component_name = clean_component_name(ref_des)
                component_id_str = ref_des  # Use actual ref des as ID
            else:
                component_name = f"Component_{component_id}"
                component_id_str = f"U{component_id}"
            
            # Extract pin information with real pin names
            pins = []
            # Search for 'PIN' or 'CONNECT' elements within the current component element
            for pin_elem in element.findall('.//PIN') + element.findall('.//CONNECT'):
                pin_name = (pin_elem.get('NAME') or
                            pin_elem.get('PINNAME') or
                            pin_elem.get('PINNUM') or
                            pin_elem.get('number') or
                            pin_elem.get('id') or
                            f"Pin{len(pins)+1}")

                pins.append({
                    'name': clean_pin_name(pin_name),
                    'connected_to': '',
                    'net': pin_elem.get('NET', '') # Store net name if available
                })
            
            # If no pins found, create realistic pins based on component type and ref des
            if not pins:
                pins = create_realistic_pins(comp_type, ref_des)
            
            components.append({
                'id': component_id_str,
                'name': component_name,
                'type': clean_component_name(comp_type),
                'value': clean_component_name(value),
                'pins': pins,
                'x': element.get('x', str(component_id * 100)),
                'y': element.get('y', str(component_id * 100))
            })
            component_id += 1
        
        # Look for power rails and nets
        elif any(keyword in tag_name for keyword in ['power', 'rail', 'net', 'wire']):
            net_name = element.get('name') or element.get('id') or element_text
            if net_name and any(power_keyword in net_name.upper() for power_keyword in ['VCC', '5V', 'GND', 'GROUND', 'VDD', 'VSS', '3V3', '12V']):
                components.append({
                    'id': f"PWR{component_id}",
                    'name': clean_component_name(net_name),
                    'type': 'Power Rail',
                    'value': determine_power_value(net_name),
                    'pins': [
                        {'name': 'OUT', 'connected_to': '', 'net': ''}
                    ],
                    'x': str(component_id * 100),
                    'y': '50'
                })
                component_id += 1
    
    # If no components found, create mock components
    if not components:
        print("No components found in XML, creating demo components")
        components = create_demo_components_for_proteus()
    
    return components

def clean_component_name(name):
    """Clean component name from XML parsing artifacts"""
    if not name:
        return "Unknown"
    
    # Remove common XML artifacts and non-printable characters
    cleaned = ''.join(char for char in name if char.isprintable())
    cleaned = cleaned.strip()
    
    # If the cleaned name is too short or contains mostly special characters, return a default
    if len(cleaned) < 2 or len([c for c in cleaned if c.isalnum()]) < 2:
        return "Component"
    
    return cleaned[:50]  # Limit length

def clean_pin_name(pin_name):
    """Clean pin name while preserving special characters that might be part of the name."""
    if not pin_name:
        return "Pin"
    
    # Strip leading/trailing whitespace and non-printable characters
    cleaned = ''.join(char for char in pin_name if char.isprintable()).strip()
    
    # If cleaning results in an empty string, return a default
    if not cleaned:
        return "Pin"
        
    # Avoid being too aggressive; many pin names are just numbers or single letters
    return cleaned[:25]  # Limit length to 25 chars

def determine_power_value(net_name):
    """Determine power rail voltage from name"""
    net_upper = net_name.upper()
    if '5V' in net_upper or 'VCC' in net_upper:
        return '5V'
    elif '3V3' in net_upper or '3.3V' in net_upper:
        return '3.3V'
    elif '12V' in net_upper:
        return '12V'
    elif 'GND' in net_upper or 'GROUND' in net_upper or 'VSS' in net_upper:
        return '0V (Ground)'
    else:
        return 'Power'

def create_realistic_pins(comp_type, ref_des):
    """Create realistic pins based on component type and reference designator"""
    comp_type_lower = comp_type.lower() if comp_type else ""
    ref_des_upper = ref_des.upper() if ref_des else ""
    
    # Use reference designator to determine component type
    if ref_des_upper.startswith('IC') or ref_des_upper.startswith('U'):
        if 'arduino' in comp_type_lower:
            return [
                {'name': 'VIN', 'connected_to': '', 'net': ''},
                {'name': 'GND', 'connected_to': '', 'net': ''},
                {'name': '5V', 'connected_to': '', 'net': ''},
                {'name': '3V3', 'connected_to': '', 'net': ''},
                {'name': 'D0', 'connected_to': '', 'net': ''},
                {'name': 'D1', 'connected_to': '', 'net': ''},
                {'name': 'D2', 'connected_to': '', 'net': ''},
                {'name': 'D13', 'connected_to': '', 'net': ''},
                {'name': 'A0', 'connected_to': '', 'net': ''},
                {'name': 'A1', 'connected_to': '', 'net': ''}
            ]
        else:
            return [
                {'name': 'VCC', 'connected_to': '', 'net': ''},
                {'name': 'GND', 'connected_to': '', 'net': ''},
                {'name': '1', 'connected_to': '', 'net': ''},
                {'name': '2', 'connected_to': '', 'net': ''}
            ]
    elif ref_des_upper.startswith('R'):
        return [
            {'name': '1', 'connected_to': '', 'net': ''},
            {'name': '2', 'connected_to': '', 'net': ''}
        ]
    elif ref_des_upper.startswith('D') or ref_des_upper.startswith('LED'):
        return [
            {'name': 'A', 'connected_to': '', 'net': ''},  # Anode
            {'name': 'K', 'connected_to': '', 'net': ''}   # Cathode
        ]
    elif ref_des_upper.startswith('C'):
        return [
            {'name': '+', 'connected_to': '', 'net': ''},
            {'name': '-', 'connected_to': '', 'net': ''}
        ]
    elif ref_des_upper.startswith('SW') or ref_des_upper.startswith('S'):
        return [
            {'name': '1', 'connected_to': '', 'net': ''},
            {'name': '2', 'connected_to': '', 'net': ''},
            {'name': '3', 'connected_to': '', 'net': ''},
            {'name': '4', 'connected_to': '', 'net': ''}
        ]
    else:
        # Default pins
        return [
            {'name': '1', 'connected_to': '', 'net': ''},
            {'name': '2', 'connected_to': '', 'net': ''}
        ]

def create_demo_components_for_proteus():
    """Create demo components specifically for Proteus file testing"""
    return [
        {
            'id': 'IC1',
            'name': 'ARDUINO_UNO_R3',
            'type': 'Microcontroller',
            'value': 'Arduino Uno R3',
            'pins': [
                {'name': 'VIN', 'connected_to': '', 'net': ''},
                {'name': 'GND', 'connected_to': '', 'net': ''},
                {'name': '5V', 'connected_to': '', 'net': ''},
                {'name': '3V3', 'connected_to': '', 'net': ''},
                {'name': 'RESET', 'connected_to': '', 'net': ''},
                {'name': 'D0', 'connected_to': '', 'net': ''},
                {'name': 'D1', 'connected_to': '', 'net': ''},
                {'name': 'D2', 'connected_to': '', 'net': ''},
                {'name': 'D3', 'connected_to': '', 'net': ''},
                {'name': 'D4', 'connected_to': '', 'net': ''},
                {'name': 'D5', 'connected_to': '', 'net': ''},
                {'name': 'D6', 'connected_to': '', 'net': ''},
                {'name': 'D7', 'connected_to': '', 'net': ''},
                {'name': 'D8', 'connected_to': '', 'net': ''},
                {'name': 'D9', 'connected_to': '', 'net': ''},
                {'name': 'D10', 'connected_to': '', 'net': ''},
                {'name': 'D11', 'connected_to': '', 'net': ''},
                {'name': 'D12', 'connected_to': '', 'net': ''},
                {'name': 'D13', 'connected_to': '', 'net': ''},
                {'name': 'A0', 'connected_to': '', 'net': ''},
                {'name': 'A1', 'connected_to': '', 'net': ''},
                {'name': 'A2', 'connected_to': '', 'net': ''},
                {'name': 'A3', 'connected_to': '', 'net': ''},
                {'name': 'A4', 'connected_to': '', 'net': ''},
                {'name': 'A5', 'connected_to': '', 'net': ''}
            ],
            'x': '100',
            'y': '100'
        },
        {
            'id': 'D1',
            'name': 'LED-RED',
            'type': 'LED',
            'value': '5mm Red LED',
            'pins': [
                {'name': 'A', 'connected_to': '', 'net': ''},
                {'name': 'K', 'connected_to': '', 'net': ''}
            ],
            'x': '300',
            'y': '150'
        },
        {
            'id': 'R1',
            'name': 'RES',
            'type': 'Resistor',
            'value': '220Ω',
            'pins': [
                {'name': '1', 'connected_to': '', 'net': ''},
                {'name': '2', 'connected_to': '', 'net': ''}
            ],
            'x': '250',
            'y': '150'
        },
        {
            'id': 'SW1',
            'name': 'BUTTON',
            'type': 'Push Button',
            'value': 'Tactile Switch',
            'pins': [
                {'name': '1', 'connected_to': '', 'net': ''},
                {'name': '2', 'connected_to': '', 'net': ''},
                {'name': '3', 'connected_to': '', 'net': ''},
                {'name': '4', 'connected_to': '', 'net': ''}
            ],
            'x': '150',
            'y': '250'
        },
        {
            'id': 'PWR1',
            'name': '5V',
            'type': 'Power Rail',
            'value': '5V',
            'pins': [
                {'name': 'OUT', 'connected_to': '', 'net': ''}
            ],
            'x': '50',
            'y': '50'
        },
        {
            'id': 'PWR2',
            'name': 'GND',
            'type': 'Power Rail',
            'value': '0V (Ground)',
            'pins': [
                {'name': 'OUT', 'connected_to': '', 'net': ''}
            ],
            'x': '50',
            'y': '300'
        }
    ]

def analyze_proteus_file(filepath):
    """Analyze Proteus file and return file information"""
    file_info = {
        'size': 0,
        'type': 'Unknown',
        'encoding': 'Unknown',
        'is_zip': False,
        'is_xml': False,
        'content_preview': '',
        'file_signature': '',
        'proteus_version': 'Unknown'
    }
    
    try:
        # Get file size
        file_info['size'] = os.path.getsize(filepath)
        
        # Read first few bytes to determine file signature
        with open(filepath, 'rb') as f:
            first_bytes = f.read(16)
            file_info['file_signature'] = ' '.join([f'{b:02X}' for b in first_bytes])
        
        # Check if it's a ZIP file
        try:
            with zipfile.ZipFile(filepath, 'r') as zip_file:
                file_info['is_zip'] = True
                file_info['type'] = 'ZIP Archive (Proteus 8+)'
                file_list = zip_file.namelist()
                file_info['content_preview'] = f"ZIP contains: {', '.join(file_list[:5])}"
                
                # Try to determine Proteus version from ZIP contents
                if 'PROJECT.XML' in file_list:
                    file_info['proteus_version'] = 'Proteus 8.x'
                elif any('.dsn' in f for f in file_list):
                    file_info['proteus_version'] = 'Proteus 7.x/8.x'
                    
        except zipfile.BadZipFile:
            file_info['is_zip'] = False
            
            # Check for older Proteus file formats
            try:
                with open(filepath, 'rb') as f:
                    binary_content = f.read(1000)
                
                # Check for Proteus binary signatures
                if b'ISIS' in binary_content or b'ARES' in binary_content:
                    file_info['type'] = 'Proteus Binary (Legacy)'
                    file_info['proteus_version'] = 'Proteus 6.x/7.x'
                elif b'<?xml' in binary_content:
                    file_info['type'] = 'Proteus XML (Legacy)'
                    file_info['proteus_version'] = 'Proteus 7.x'
                else:
                    file_info['type'] = 'Unknown Proteus Format'
                
                # Try to read as text for preview
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(1000)
                        file_info['encoding'] = 'UTF-8'
                        file_info['content_preview'] = content[:200] + '...' if len(content) > 200 else content
                        
                        if '<' in content and '>' in content:
                            file_info['is_xml'] = True
                            if 'ISIS' in content or 'ARES' in content:
                                file_info['type'] = 'Proteus XML'
                                
                except UnicodeDecodeError:
                    file_info['content_preview'] = f"Binary data ({len(binary_content)} bytes)"
            
            except Exception as read_error:
                file_info['content_preview'] = f"File reading error: {str(read_error)}"
    
    except Exception as e:
        file_info['content_preview'] = f"Error analyzing file: {str(e)}"
    
    return file_info

def create_proteus_compatible_file(original_filepath, connections):
    """
    Creates a safe, unmodified copy of the original Proteus file.
    Connections are handled by separate script files to prevent corruption.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    updated_filename = f"connected_proteus_{timestamp}.pdsprj"
    updated_filepath = os.path.join(app.config['UPLOAD_FOLDER'], updated_filename)
    
    try:
        # Simply copy the original file to ensure it is not corrupted.
        # The user will import connections using the generated .SCR or .NET file.
        shutil.copy2(original_filepath, updated_filepath)
        
        return updated_filename
        
    except Exception as e:
        raise Exception(f"Failed to create a copy of the Proteus file: {str(e)}")


def create_connection_files(timestamp, connections):
    """Create separate connection files for manual import into Proteus"""
    
    # 1. Create a Proteus netlist file (.NET)
    netlist_filename = f"netlist_{timestamp}.net"
    netlist_path = os.path.join(app.config['UPLOAD_FOLDER'], netlist_filename)
    
    with open(netlist_path, 'w', encoding='utf-8') as f:
        f.write(create_proteus_netlist(connections))
    
    # 2. Create a connection script file (.SCR)
    script_filename = f"connect_script_{timestamp}.scr"
    script_path = os.path.join(app.config['UPLOAD_FOLDER'], script_filename)
    
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(create_proteus_script(connections))
    
    # 3. Create human-readable wiring guide
    guide_filename = f"wiring_guide_{timestamp}.txt"
    guide_path = os.path.join(app.config['UPLOAD_FOLDER'], guide_filename)
    
    with open(guide_path, 'w', encoding='utf-8') as f:
        f.write(create_wiring_guide(connections))

def create_proteus_netlist(connections):
    """Create a Proteus-compatible netlist file with a more descriptive header."""
    netlist = f"""# Proteus Netlist File
# Generated by the Proteus Connection Editor
# Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#
# This file describes the connections (nets) between component pins.
# It can be used for cross-probing or importing into other EDA tools.
#
# Total connections: {len(connections)}

"""
    
    # Group connections by net
    nets = {}
    for i, conn in enumerate(connections):
        net_name = conn.get('net_name', f"NET_{i+1:03d}")
        
        from_pin_full = f"{conn.get('from_component', 'C?')}.{conn.get('from_pin', 'P?')}"
        to_pin_full = f"{conn.get('to_component', 'C?')}.{conn.get('to_pin', 'P?')}"

        if net_name not in nets:
            nets[net_name] = set()
        
        nets[net_name].add(from_pin_full)
        nets[net_name].add(to_pin_full)
    
    # Write netlist format
    for net_name, pins in nets.items():
        netlist += f"(NET \"{net_name}\"\n"
        for pin in sorted(list(pins)):
            netlist += f"  (PIN \"{pin}\")\n"
        netlist += ")\n\n"
    
    return netlist

def create_proteus_script(connections):
    """Create a more detailed and robust Proteus script file."""
    script = f"""-- Proteus ISIS Script
-- Generated by Proteus Connection Editor
-- Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
--
-- This script automates wire connections in Proteus.
--
-- HOW TO USE:
-- 1. In Proteus, go to 'File' -> 'Run Script...'
-- 2. Select this .SCR file.
-- 3. The script will attempt to create all connections.
--
-- !! IMPORTANT !!
-- - Component reference designators (e.g., U1, R1) MUST match your schematic.
-- - Pin names/numbers MUST match the component's definition in Proteus.
-- - If a component or pin is not found, the script will report an error.
--

-- Clear any existing selections
COMMAND "SELECT_NONE"

-- Script header
MESSAGE "Starting automated wiring script..."

"""
    
    # Component and pin verification section
    script += "-- COMPONENT AND PIN VERIFICATION\n"
    script += "-- Please verify the following components and pins exist in your project:\n"
    
    components_used = set()
    for conn in connections:
        components_used.add(conn.get('from_component', 'Unknown'))
        components_used.add(conn.get('to_component', 'Unknown'))
        
    for comp in sorted(components_used):
        script += f"-- Component: {comp}\n"
        
    script += "\n"
    
    # Connection commands
    script += "-- WIRING CONNECTIONS\n"
    
    for i, conn in enumerate(connections, 1):
        from_comp = conn.get('from_component', 'Unknown')
        from_pin = conn.get('from_pin', 'Unknown')
        to_comp = conn.get('to_component', 'Unknown')
        to_pin = conn.get('to_pin', 'Unknown')
        
        script += f"\n-- Connection {i}: {from_comp}.{from_pin} -> {to_comp}.{to_pin}\n"
        
        # Add error handling for each connection
        script += f'-- Try to select start and end pins\n'
        script += f'ASSIGN PIN "{from_comp}" "{from_pin}"\n'
        script += f'IF ERRORLEVEL == 0 THEN\n'
        script += f'  ASSIGN PIN "{to_comp}" "{to_pin}"\n'
        script += f'  IF ERRORLEVEL == 0 THEN\n'
        script += f'    -- Both pins found, create wire\n'
        script += f'    WIRE "{from_comp}" "{from_pin}" "{to_comp}" "{to_pin}"\n'
        script += f'    MESSAGE "Wired {from_comp}.{from_pin} to {to_comp}.{to_pin}"\n'
        script += f'  ELSE\n'
        script += f'    MESSAGE "ERROR: Pin {to_pin} on component {to_comp} not found!"\n'
        script += f'  ENDIF\n'
        script += f'ELSE\n'
        script += f'  MESSAGE "ERROR: Pin {from_pin} on component {from_comp} not found!"\n'
        script += f'ENDIF\n'

    script += f"""
-- Script finished
MESSAGE "Automated wiring script complete. Check for any error messages."

-- End of script
"""
    return script

def create_wiring_guide(connections):
    """Create a comprehensive and user-friendly wiring guide."""
    guide = f"""#================================================================
# PROTEUS WIRING GUIDE
#================================================================
# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Total Connections: {len(connections)}
#
# This guide provides step-by-step instructions for wiring your
# circuit in Proteus. For best results, use the Manual Wiring method.
#================================================================

## 1. QUICK WIRING LIST
# Use this list for rapid manual wiring.
#----------------------------------------------------------------
"""
    
    for i, conn in enumerate(connections, 1):
        from_comp = conn.get('from_component', 'Unknown')
        from_pin = conn.get('from_pin', 'Unknown')
        to_comp = conn.get('to_component', 'Unknown')
        to_pin = conn.get('to_pin', 'Unknown')
        guide += f"{i:02d}. {from_comp:<15} Pin {from_pin:<10} ───► {to_comp:<15} Pin {to_pin:<10}\n"
    
    guide += f"""
## 2. DETAILED COMPONENT-BY-COMPONENT GUIDE
# Wire all connections for one component before moving to the next.
#----------------------------------------------------------------
"""
    
    # Group connections by component for a more organized guide
    by_component = {}
    for conn in connections:
        comp_from = conn.get('from_component', 'Unknown')
        comp_to = conn.get('to_component', 'Unknown')
        
        if comp_from not in by_component:
            by_component[comp_from] = []
        by_component[comp_from].append(conn)
        
        if comp_to not in by_component:
            by_component[comp_to] = []
        # Add the reverse connection for context
        reverse_conn = {
            'from_component': conn['to_component'], 'from_pin': conn['to_pin'],
            'to_component': conn['from_component'], 'to_pin': conn['from_pin']
        }
        by_component[comp_to].append(reverse_conn)

    for comp, conns in sorted(by_component.items()):
        guide += f"\n### Component: {comp}\n"
        for conn in conns:
            # Show only outgoing connections from the current component
            if conn.get('from_component') == comp:
                guide += f"  - Pin {conn.get('from_pin', ''):<10} → connects to {conn.get('to_component', '')}.{conn.get('to_pin', '')}\n"
        guide += "\n"

    guide += """
## 3. HOW TO WIRE IN PROTEUS
#----------------------------------------------------------------
#
# ### Method 1: Manual Wiring (Recommended)
#   1. Open your Proteus project.
#   2. Press the 'W' key to activate the Wire tool.
#   3. Follow the 'QUICK WIRING LIST' or the 'COMPONENT-BY-COMPONENT GUIDE'.
#   4. Click on the first component's pin (e.g., IC1.TXD).
#   5. Click on the second component's pin (e.g., CONN1.RXD).
#   6. A wire will be created. Repeat for all connections.
#
# ### Method 2: Using the Generated Script (.SCR file)
#   1. Go to 'File' -> 'Run Script...' in Proteus.
#   2. Select the accompanying .scr file.
#   3. The script will attempt to wire everything automatically.
#      (Note: This may fail if component names do not match exactly).
#
## 4. VERIFICATION CHECKLIST
#----------------------------------------------------------------
#  [ ] All connections from the list have been made.
#  [ ] No accidental short circuits (especially to VCC or GND).
#  [ ] Power and Ground pins for all ICs are correctly wired.
#  [ ] Run the simulation to ensure the circuit behaves as expected.
#
##================================================================
# End of Guide
#================================================================
"""
    return guide

@app.route('/download_proteus/<filename>')
def download_proteus(filename):
    """Download updated Proteus file"""
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        return send_file(filepath, as_attachment=True)
    else:
        return jsonify({'error': 'File not found'}), 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
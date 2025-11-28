#!/bin/bash
# Setup script for Arabic Legal Documents OCR System

echo "======================================"
echo "Arabic Legal Documents OCR System"
echo "Setup Script"
echo "======================================"

# Check Python version
echo "Checking Python version..."
python3 --version

if [ $? -ne 0 ]; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Check for poppler
echo "Checking for Poppler..."
if command -v pdfinfo &> /dev/null; then
    echo "✓ Poppler is installed"
else
    echo "⚠ Poppler is not installed"
    echo "Please install Poppler:"
    echo "  - Ubuntu/Debian: sudo apt-get install poppler-utils"
    echo "  - macOS: brew install poppler"
fi

# Check for CUDA
echo "Checking for CUDA..."
if command -v nvidia-smi &> /dev/null; then
    echo "✓ CUDA is available"
    nvidia-smi --query-gpu=name,memory.total --format=csv
else
    echo "⚠ CUDA not detected. GPU acceleration will be disabled."
fi

# Initialize database
echo "Initializing database..."
python -c "from src.models.database import init_db; init_db()"

# Create .env template
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cat > .env << EOL
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_CREDENTIALS_PATH=credentials.json
EOL
    echo "✓ .env template created"
    echo "Please edit .env and add your Google Drive folder ID"
fi

echo "======================================"
echo "✓ Setup completed successfully!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Download Google Drive credentials.json"
echo "2. Edit .env file with your Google Drive folder ID"
echo "3. Run: python main.py --sync"
echo "4. Run: python main.py --process"
echo ""

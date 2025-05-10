# Define the base directory
$baseDir = "fund-transfer-system"

# Define the folder structure
$folders = @(
    "config",
    "data",
    ".github",
    "logs",
    "payment_processors",
    "schemas"
)

# Define the files to create
$files = @(
    "api_service.py",
    "config/api_keys.json",
    "config/config.json",
    ".env",
    ".github/FUNDING.yml",
    "funding.json",
    "README.md",
    "requirements.txt",
    "payment_processors/__init__.py",
    "payment_processors/paypal_integration.py",
    "payment_processors/stripe_integration.py"
)

# Create the base directory if it doesn't exist
if (!(Test-Path $baseDir)) {
    New-Item -ItemType Directory -Path $baseDir
}

# Create folders
foreach ($folder in $folders) {
    $folderPath = "$baseDir/$folder"
    if (!(Test-Path $folderPath)) {
        New-Item -ItemType Directory -Path $folderPath
    }
}

# Create files
foreach ($file in $files) {
    $filePath = "$baseDir/$file"
    if (!(Test-Path $filePath)) {
        New-Item -ItemType File -Path $filePath
    }
}

Write-Output "Fund transfer system structure has been set up successfully!"

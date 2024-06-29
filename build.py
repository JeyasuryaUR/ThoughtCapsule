import subprocess

def run_command(command):
    """Run a shell command and check if it was successful."""
    result = subprocess.run(command, shell=True)
    if result.returncode != 0:
        print(f"Command {' '.join(command)} failed with exit code {result.returncode}")
        exit(result.returncode)

# Install requirements
run_command("pip install -r requirements.txt")

# Convert static asset files
run_command("python manage.py collectstatic --no-input")

# Apply any outstanding database migrations
run_command("python manage.py migrate")

# Download Spacy language model
run_command("python -m spacy download en_core_web_sm")

print("Build process completed successfully.")
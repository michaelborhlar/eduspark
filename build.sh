#!/usr/bin/env bash
set -o errexit

echo ">>> Python version:"
python --version

echo ">>> Installing dependencies..."
pip install -r requirements.txt

echo ">>> Creating required directories..."
mkdir -p static staticfiles media

echo ">>> Collecting static files..."
python manage.py collectstatic --noinput

echo ">>> Making migrations (auto-generate from models)..."
python manage.py makemigrations core --noinput

echo ">>> Running migrations..."
python manage.py migrate --noinput

echo ">>> Seeding subjects..."
python manage.py shell -c "
from core.models import Subject
subjects = [
    'Mathematics', 'English Language', 'Literature in English',
    'Biology', 'Chemistry', 'Physics',
    'Government', 'Economics', 'Geography',
    'Agricultural Science', 'Computer Science', 'Further Mathematics',
    'Civic Education', 'Christian Religious Studies', 'Islamic Religious Studies',
]
created = 0
for name in subjects:
    _, made = Subject.objects.get_or_create(name=name)
    if made:
        created += 1
print(f'Subjects ready: {Subject.objects.count()} total ({created} new)')
"

echo ">>> Build complete!"

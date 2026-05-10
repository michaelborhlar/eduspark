#!/usr/bin/env bash
# Render build script
set -o errexit

pip install -r requirements.txt

# Create static dir if missing so collectstatic doesn't warn
mkdir -p static staticfiles media

python manage.py collectstatic --noinput
python manage.py migrate

# Seed subjects automatically on first deploy
python manage.py shell << 'PYEOF'
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
print(f"Subjects ready: {Subject.objects.count()} total ({created} new)")
PYEOF

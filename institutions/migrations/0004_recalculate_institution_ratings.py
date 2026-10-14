from django.db import migrations
from django.db.models import Avg, Count


def recalculate_ratings(apps, schema_editor):
    Institution = apps.get_model('institutions', 'Institution')
    Review = apps.get_model('institutions', 'Review')
    database = schema_editor.connection.alias
    ratings = {
        row['institution_id']: row
        for row in Review.objects.using(database).filter(is_removed=False)
        .values('institution_id')
        .annotate(average=Avg('rating'), count=Count('id'))
    }
    institutions = list(Institution.objects.using(database).all())
    for institution in institutions:
        summary = ratings.get(institution.pk)
        institution.rating = summary['average'] if summary else 0
        institution.rating_count = summary['count'] if summary else 0
    Institution.objects.using(database).bulk_update(institutions, ('rating', 'rating_count'))


class Migration(migrations.Migration):

    dependencies = [
        ('institutions', '0003_program_direction'),
    ]

    operations = [
        migrations.RunPython(recalculate_ratings, migrations.RunPython.noop),
    ]
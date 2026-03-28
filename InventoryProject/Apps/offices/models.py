from django.db import models


DEFAULT_FLOORS_BY_OFFICE = {
    'nasan': ['1st Floor', '2nd Floor', '3rd Floor', '4th Floor', '5th Floor'],
    'aasan': ['10th Floor', '11th Floor'],
    'katraj': [],
}


class Office(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    floor_choices = models.TextField(
        blank=True,
        default='',
        help_text='Optional custom floors or areas, separated by commas or new lines.',
    )

    def get_floor_options(self):
        configured = [
            floor.strip()
            for floor in self.floor_choices.replace(',', '\n').splitlines()
            if floor.strip()
        ]
        if configured:
            return configured

        office_name = self.name.lower()
        for office_key, floors in DEFAULT_FLOORS_BY_OFFICE.items():
            if office_key in office_name:
                return floors.copy()
        return []

    def __str__(self):
        return self.name

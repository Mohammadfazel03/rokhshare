from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import ValidationError
from rest_framework.utils.representation import smart_repr

from movie.models import Media


class OneFieldsSet:
    message = _('The fields {field_names} must make a unique set.')
    missing_message = _('One of this fields {field_names} must be set')
    requires_context = True

    def __init__(self, fields, message=None):
        self.fields = fields
        self.message = message or self.message

    def __call__(self, attrs, serializer):
        if serializer.instance is not None:
            return

        set_items = []

        for field_name in self.fields:
            if serializer.fields[field_name].source in attrs:
                set_items.append(field_name)

        if len(set_items) == 0:
            missing_items = {
                field_name: self.missing_message.format(field_names=', '.join(self.fields))
                for field_name in self.fields
            }

            raise ValidationError(missing_items, code='required')
        elif len(set_items) > 1:
            field_names = ', '.join(set_items)
            message = self.message.format(field_names=field_names)
            raise ValidationError(message, code='unique')

    def __repr__(self):
        return '<%s(fields=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.fields)
        )


class MediaEpisodeValidator:
    message = _('The fields episode, media are not compatible with each other.')
    requires_context = True

    def __init__(self, message=None):
        self.message = message or self.message

    def __call__(self, attrs, serializer):
        episode = attrs.get('episode', None)
        if episode:
            if attrs['media'] != Media.objects.get(tvseries__season__episode=episode):
                raise ValidationError(self.message)
        print()



    def __repr__(self):
        return '<%s(fields=%s)>' % (
            self.__class__.__name__,
            smart_repr(self.fields)
        )

# This file is a part of MediaCore, Copyright 2009 Simple Station Inc.
#
# MediaCore is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# MediaCore is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from pylons import request
from pylons.i18n import N_ as _
from tw.forms import PasswordField, SingleSelectField
from tw.forms.fields import ContainerMixin as _ContainerMixin
from tw.forms.validators import All, FancyValidator, FieldsMatch, Invalid, NotEmpty, PlainText, Schema

from mediacore.forms import ListFieldSet, ListForm, SubmitButton, TextField
from mediacore.plugin import events
from mediacore.plugin.abc import abstractmethod

class StorageForm(ListForm):
    template = 'admin/box-form.html'
    id = 'storage-form'
    css_class = 'form storageform'
    submit_text = None
    show_children_errors = True
    _name = 'storage-form' # TODO: Figure out why this is required??
    params = ['engine']

    fields = [
        ListFieldSet('general',
            legend=_('General Options:'),
            suppress_label=True,
            children=[
                TextField('display_name',
                    label_text=_('Display Name'),
                    validator=TextField.validator(not_empty=True),
                    maxlength=100,
                ),
            ],
        ),
    ]

    buttons = [
        SubmitButton('save',
            default=_('Save'),
            named_button=True,
            css_classes=['btn', 'btn-save', 'blue', 'f-rgt'],
        ),
        SubmitButton('delete',
            default=_('Delete'),
            named_button=True,
            css_classes=['btn', 'btn-delete', 'f-lft'],
        ),
    ]

    def display(self, value, **kwargs):
        """Display the form with default values from the engine param."""
        engine = kwargs['engine']
        general = value.setdefault('general', {})
        if not general.get('display_name', None):
            general['display_name'] = engine.display_name
        return ListForm.display(self, value, **kwargs)

    def save_engine_params(self, engine, general, **kwargs):
        """Map validated field values to engine data.

        Since form widgets may be nested or named differently than the keys
        in the :attr:`mediacore.lib.storage.StorageEngine._data` dict, it is
        necessary to manually map field values to the data dictionary.

        :type engine: :class:`mediacore.lib.storage.StorageEngine` subclass
        :param engine: An instance of the storage engine implementation.
        :param \*\*kwargs: Validated and filtered form values.
        :raises formencode.Invalid: If some post-validation error is detected
            in the user input. This will trigger the same error handling
            behaviour as with the @validate decorator.

        """
        engine.display_name = general['display_name']

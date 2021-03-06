import unittest
from freeplane_importer.importer import Importer
from mock import Mock
from mock import MagicMock
from mock import call

from freeplane_importer.model_not_found_exception import ModelNotFoundException


class TestImporter(unittest.TestCase):

    def setUp(self):
        self.mock_collection = Mock()

        self.mock_model = MagicMock()
        self.mock_collection.models.byName.return_value = self.mock_model

        self.mock_note = MagicMock()
        self.mock_note.model.return_value = self.mock_model
        self.mock_collection.newNote.return_value = self.mock_note

        self.mock_collection.models.fieldNames.return_value = []

        self.importer = Importer(self.mock_collection)

        self.mock_collection.db.scalar.return_value = None

        self.note = {
            'id': 100,
            'deck': 'History',
            'model': 'Basic',
            'fields': {}
        }

    def test_it_should_initialise_the_correct_model(self):
        self.importer.import_note(self.note)
        self.mock_collection.models.setCurrent.assert_called_with(
            self.mock_model)

    def test_it_should_select_the_correct_deck(self):
        self.mock_collection.decks.id.return_value = 100
        self.importer = Importer(self.mock_collection)
        self.importer.import_note(self.note)
        self.mock_model.__setitem__.assert_called_with('did', 100)
        self.mock_collection.decks.id.assert_called_with('History')

    def test_it_should_find_the_correct_model(self):
        self.importer.import_note(self.note)
        self.mock_collection.models.byName.assert_called_with('Basic')

    def test_it_should_return_true_if_note_was_added_successfully(self):
        self.assertTrue(self.importer.import_note(self.note))

    def test_it_should_raise_a_no_model_exception_if_the_model_does_not_exist(self):
        self.mock_collection.models.byName.return_value = None
        self.assertRaises(ModelNotFoundException,
                          self.importer.import_note, self.note)

    def test_it_should_create_a_new_note(self):
        self.importer.import_note(self.note)
        self.mock_collection.newNote.assert_called_with()

    def test_it_should_get_the_field_names_from_the_model(self):
        self.importer.import_note(self.note)
        self.mock_collection.models.fieldNames.assert_called_with(
            self.mock_model)

    def test_it_should_save_the_node_id_if_the_first_field_is_named_id_in_lowercase(self):
        self.mock_collection.models.fieldNames.return_value = ['id']
        self.importer.import_note(self.note)

        self.mock_note.__setitem__.assert_called_with('id', 100)

    def test_it_should_save_the_node_id_if_the_first_field_is_named_id_in_uppercase(self):
        self.mock_collection.models.fieldNames.return_value = ['ID']
        self.importer.import_note(self.note)

        self.mock_note.__setitem__.assert_called_with('ID', 100)

    def test_it_should_populate_the_note_with_the_field_values(self):
        self.note['fields'] = {
            'Front': 'Front value',
            'Back': 'Back value'
        }

        self.mock_collection.models.fieldNames.return_value = ['Front', 'Back']
        self.importer.import_note(self.note)

        self.mock_note.__setitem__.assert_has_calls(
            [call('Front', 'Front value'), call('Back', 'Back value')])

    def test_it_should_ignore_fields_that_do_not_exist_in_the_model(self):
        self.note['fields'] = {
            'Front': 'Front value',
            'Back': 'Back value'
        }

        self.mock_collection.models.fieldNames.return_value = ['Front']
        self.importer.import_note(self.note)
        self.assertFalse('Back' in self.mock_note)

    def test_it_should_save_the_note_changes(self):
        self.importer.import_note(self.note)
        self.mock_note.flush.assert_called_with()

    def test_it_should_attempt_to_find_an_existing_note_with_the_given_node_id(self):
        self.mock_collection.getNote.return_value = self.mock_note
        self.mock_collection.db.scalar.return_value = 123

        self.importer.import_note(self.note)
        self.mock_collection.getNote.assert_called_with(123)

    def test_it_should_add_the_note_to_the_collection_if_it_is_new(self):
        del self.mock_note.mod
        self.importer.import_note(self.note)
        self.mock_collection.addNote.assert_called_with(self.mock_note)

    def test_it_should_not_add_the_note_to_the_collection_if_it_is_not_new(self):
        self.importer.import_note(self.note)
        self.assertEqual(0, self.mock_collection.addNote.call_count)
